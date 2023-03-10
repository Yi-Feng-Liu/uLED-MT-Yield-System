import matplotlib 
matplotlib.use('agg') 
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
from datetime import timedelta
import schedule
import logging
import os
from utils._CreatePPt_ import PPTmain
import shutil
from utils.sendMail import auto_mail, customMessageAutoMail
import time
import numpy as np
from decimal import Decimal, ROUND_HALF_UP
from SFTP.Connection import getLightOnResult


# plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
# plt.rcParams['axes.unicode_minus'] = False
class TableType():
    """Created table will be send by email.

    All of table type function in this class, including table by sheet, table by hours, table by day, table by week, table by month.
    """
    def __init__(self):
        self.key_list = ['CreateTime', 'OPID', 'Defect_Code', 'SHEET_ID', 'LED_TYPE', 'NGCNT', 'YiledAnalysis_2D', 'Process_OK', 'Process_NG', 'NO_Process_OK', 'NO_Process_NG', 'Bond_Success_Rate', 'Lighting_Rate']
        self.fontsize = 14
        self.R_color = 'fuchsia'
        self.G_color = 'mediumseagreen'
        self.B_color = 'blue'
        self.logPath = './log/'
        self.reportImgPath = './report_production/'
        self.summaryTablePath = '../table/SummaryTable.csv'
        self.OPID_comparison_table = {
            'CNAPL':'CO-M-AOI Plasma',
            'CRAPL':'CO-R-AOI Plasma', 
            'TNAB2':'TFT-M-AOI Shiping',
            'TNABO':'TFT-M-AOI Bonding',
            'TNACL':'TFT-M-AOI Clean',
            'TNLAT':'TFT-M-light ATC',
            'TNLBO':'TFT-M-light Bonding',
            'UM-BON':'TFT-M-light Bonding',
            'TNLCL':'TFT-M-light CLN for Ship',
            'TNLLA':'TFT-M-light Laser cut',
            'TNLPL':'TFT-M-light Plasma',
            'TRADE':'TFT-R-AOI Debond',
            'TRARE':'TFT-R-AOI Repair-Bond',
            'TRLAG':'TFT-R-light Aging',
            'TRLLM':'TFT-R-light LSMT',
            'TRLRE':'TFT-R-light Repair-Bond',
            'UM-CLN': 'UM-CLN'
        }
        self.RGB_ls={
            'R':'R',
            'G':'G',
            'B':'B'
        }

        self.labels = ["R_Process_NG", "R_No_Process_NG", "R_Process_OK", "G_Process_NG", "G_No_Process_NG", "G_Process_OK", "B_Process_NG", "B_No_Process_NG", "B_Process_OK"]
        self.table_and_fig_gap = -0.55
        self.color_dict = {
                'R_NG': 'fuchsia',
                'G_NG': 'mediumseagreen',
                'B_NG': 'blue',
                'R_Yield': 'fuchsia', 
                'G_Yield': 'mediumseagreen', 
                'B_Yield': 'blue',
                'MB_Yield': 'black'
            }


    def CreateLog(self, fileName, logPath):
        if not os.path.exists(logPath):
            os.mkdir(logPath)
            logging.basicConfig(
                filename= f'./log/{fileName}', 
                filemode= 'w', 
                format= '%(asctime)s - %(message)s', 
                encoding= 'utf-8'
                )
        else:
            logging.basicConfig(
                filename= f'./log/{fileName}', 
                filemode='a', 
                format='%(asctime)s - %(message)s',
                encoding='utf-8'
                )


    def readFile(self, file_path: str, MODEL: str):
        """
        If need to change the report of model, please enter the product size.
        """
        df = pd.read_csv(file_path, delimiter=',')
        df = df.sort_values(by=['CreateTime'])
        # df2 = df[df.duplicated(subset=['Lighting_Rate'])].reset_index(drop=True)
        df['Defect_Code'] = df['Defect_Code'].fillna('NaN')
        df = df[df["Defect_Code"] != 'NaN']
        if str(MODEL)=='13.6':
            df = df[(~df["SHEET_ID"].str.startswith("VKV")) & (~df["SHEET_ID"].str.startswith("VXV"))]
        if str(MODEL)=='16.1':
            df = df[df["SHEET_ID"].str.startswith("VKV")]
        self.CreateLog(fileName='plotRecorder.log', logPath=self.logPath)
        return df


    def bySheet(self, df, sheetID: str):
        sheetdf = df[df["SHEET_ID"]==sheetID]
        filterSheetdf = sheetdf.filter(self.key_list)
        filterSheetdf = filterSheetdf.reset_index(drop=True)
        RGBlabel = filterSheetdf["LED_TYPE"].tolist()
        CreateTimeXticks = filterSheetdf['CreateTime'].tolist()
        return filterSheetdf, RGBlabel, CreateTimeXticks

    
    def by24hours(self, df: pd.DataFrame) -> pd.DataFrame:
        now = datetime.now().replace(minute=0).strftime('%Y%m%d%H%M')
        lastDay = (datetime.now().replace(minute=0) - timedelta(hours=24)).strftime('%Y%m%d%H%M')
        by24hours_df = df[(df.CreateTime >= int(lastDay)) & (df.CreateTime <= int(now))]
        filterSheetdf = by24hours_df.filter(self.key_list)
        filterdf = filterSheetdf[~filterSheetdf.Defect_Code.isna()].sort_values(['CreateTime', 'LED_TYPE']).drop_duplicates(['SHEET_ID', 'LED_TYPE', 'OPID'], keep='last').reset_index(drop=True)
        filterdf['CreateTime'] = filterdf.CreateTime.apply(lambda x: str(x)[:-2])
        # filterdf = filterdf[::-1]
        return now, lastDay, filterdf


    def NMB_pivot_df(self, *args, filterSheetdf:pd.DataFrame, set_values:str, set_index_column=True, **kwargs):
        """Change the data structure and return the dataframe.

        If set_index_column is True, please set the columns to and enter the column name needed.

        The column name will be assign to the args.

        The set value is select original column to become value of new dataframe 

        if need to plot report pls set the kwargs:
            
            plot_report = True
        """

        NMB_dataframe = filterSheetdf.groupby(['CreateTime', 'NGCNT', 'SHEET_ID', 'LED_TYPE', 'Bond_Success_Rate'])[['Process_OK', 'Process_NG', 'NO_Process_OK', 'NO_Process_NG']].aggregate(sum).reset_index()
        NMB_dataframe['Total_CNT'] = NMB_dataframe["Process_OK"] + NMB_dataframe['Process_NG'] + NMB_dataframe['NO_Process_OK'] + NMB_dataframe['NO_Process_NG']

        NMB_dataframe = NMB_dataframe.reset_index(drop=True)
        # print(NMB_dataframe)

        if set_index_column == True:
            recombine_df = NMB_dataframe.pivot_table(index=[*args], columns=['LED_TYPE'], values=set_values, sort=False)
        else:
            recombine_df = NMB_dataframe.pivot_table(index=[*args], columns=['LED_TYPE'], values=set_values, sort=False)
            
        recombine_df = recombine_df[['R', 'G', 'B']]
        recombine_df = recombine_df.fillna(0)
        
        for i in recombine_df.columns:
            recombine_df[str(i)] = recombine_df[str(i)].astype('int')

        recombine_df = recombine_df.reset_index()

        if set_index_column == False:
            recombine_df['R_Yield'] = ((recombine_df['Total_CNT']-recombine_df['R']) / (recombine_df['Total_CNT']))*100
            recombine_df['G_Yield'] = ((recombine_df['Total_CNT']-recombine_df['G']) / (recombine_df['Total_CNT']))*100
            recombine_df['B_Yield'] = ((recombine_df['Total_CNT']-recombine_df['B']) / (recombine_df['Total_CNT']))*100
            recombine_df['Avg_Process_Yield'] = ((recombine_df['Total_CNT']*3-recombine_df['R']-recombine_df['G']-recombine_df['B'])/(recombine_df['Total_CNT']*3))*100 

        else:
            recombine_df['R_Yield'] = ((recombine_df['Total_CNT']-recombine_df['R']) / (recombine_df['Total_CNT']))*100
            recombine_df['G_Yield'] = ((recombine_df['Total_CNT']-recombine_df['G']) / (recombine_df['Total_CNT']))*100
            recombine_df['B_Yield'] = ((recombine_df['Total_CNT']-recombine_df['B']) / (recombine_df['Total_CNT']))*100
            
            df_process_ok = NMB_dataframe.pivot_table(index=['SHEET_ID', 'CreateTime', 'Total_CNT'], columns=['LED_TYPE'], values='Process_OK', sort=False)
            
            df_process_ng = NMB_dataframe.pivot_table(index=['SHEET_ID', 'CreateTime', 'Total_CNT'], columns=['LED_TYPE'], values='Process_NG', sort=False)

            df_total = df_process_ok.merge(df_process_ng, on=['SHEET_ID', 'CreateTime', 'Total_CNT'], how='left')
            
            df_total['Avg_Process_Yield'] = (df_total['R_x'] + df_total['G_x'] + df_total['B_x']) / (df_total['R_x'] + df_total['G_x'] + df_total['B_x'] + df_total['R_y'] + df_total['G_y'] + df_total['B_y'])*100
            
            recombine_df = df_total.merge(recombine_df, on=['SHEET_ID', 'CreateTime', 'Total_CNT'], how='left')
            recombine_df = recombine_df.fillna(100)
            # ??????????????????????????????
            if kwargs.get('plot_report', False) == True:

                recombine_df['Avg_No_Process_Yield'] = (((recombine_df['Total_CNT']*3)-(recombine_df['R']+recombine_df['G']+recombine_df['B'])) / (recombine_df['Total_CNT']*3))*100

                # recombine_df['Avg_Process_Yield'] = recombine_df['Bond_Success_Rate']
                
        recombine_df['R_Yield'] = recombine_df['R_Yield'].apply(lambda x: Decimal(x).quantize(Decimal('.00'), ROUND_HALF_UP)).astype('float')    
        recombine_df['G_Yield'] = recombine_df['G_Yield'].apply(lambda x: Decimal(x).quantize(Decimal('.00'), ROUND_HALF_UP)).astype('float') 
        recombine_df['B_Yield'] = recombine_df['B_Yield'].apply(lambda x: Decimal(x).quantize(Decimal('.00'), ROUND_HALF_UP)).astype('float')
        recombine_df['Avg_Process_Yield'] = recombine_df['Avg_Process_Yield'].apply(lambda x: Decimal(x).quantize(Decimal('.00'), ROUND_HALF_UP)).astype('float')

        if set_index_column ==True & kwargs.get('plot_report', False) == True:
            
            recombine_df['Avg_No_Process_Yield'] = recombine_df['Avg_No_Process_Yield'].apply(lambda x: Decimal(x).quantize(Decimal('.00'), ROUND_HALF_UP)).astype('float')

        return recombine_df

    def byDays(self, df: pd.DataFrame) -> pd.DataFrame:
        # set period of time
        now_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        lastweek =  now_date - timedelta(days=7)

        lastweek_str = lastweek.strftime('%Y%m%d%H%M')
        now_date_str = now_date.strftime('%Y%m%d%H%M')

        # filter dataframe by columns
        filterSheetdf = df.filter(self.key_list)
        bydays_df_origin = filterSheetdf[(filterSheetdf.CreateTime >= int(lastweek_str)) & (filterSheetdf.CreateTime <= int(now_date_str))]
        bydays_df = bydays_df_origin[~bydays_df_origin.Defect_Code.isna()].sort_values(['CreateTime', 'LED_TYPE']).drop_duplicates(['SHEET_ID', 'LED_TYPE','OPID'], keep='last').reset_index(drop=True)

        # group dataframe
        bydays_df_gr = bydays_df.groupby(['CreateTime', 'OPID', 'SHEET_ID', 'LED_TYPE', 'NGCNT','YiledAnalysis_2D', 'Bond_Success_Rate'])[['Process_OK', 'Process_NG', 'NO_Process_OK', 'NO_Process_NG']].aggregate(sum).reset_index()
        # print(bydays_df_gr)
        bydays_df_gr['CreateTime'] = bydays_df_gr.CreateTime.apply(lambda x: str(x)[:-2])
        return now_date_str, lastweek_str, bydays_df_gr


    def ChooseReportType(self, summary_df, Model_type, choose_report_type:str):
        if choose_report_type.lower()=='daily':
            now_date, lastweek, res = self.by24hours(summary_df)
            figname_type = 'byPer24Hour'
        if choose_report_type.lower()=='weekly':
            now_date, lastweek, res = self.byDays(summary_df)
            figname_type = 'byDay'
            lastweek = str(lastweek).split()[0]
            now_date = str(now_date).split()[0]

        if len(res.index) != 0:
            # remove duplicate element
            resOPIDls = res.OPID.tolist()
            resOPIDls = list(dict.fromkeys(resOPIDls))
            df_ls = []
            for OPID in resOPIDls:
                if OPID == 'UM-AOI':
                    continue
                elif OPID == 'TNLBO':
                    filterdf = res[res['OPID']==OPID].reset_index(drop=True)
                    filterdf = self.NMB_pivot_df(
                        'CreateTime', 'SHEET_ID', 'Total_CNT',
                        filterSheetdf=filterdf, 
                        set_values='NGCNT', 
                        set_index_column=False,
                        plot_report = True
                    )  
                    filterdf = filterdf.drop(['Total_CNT'],  axis=1)
                    
                    df_ls.append(filterdf)
                    FullOPID = self.OPID_comparison_table.get(OPID, None)
                    if len(filterdf.index)==0:
                        continue
                    else:
                        every_date = [str(i)[4:-2] for i in filterdf.CreateTime.tolist()]
                        R_NG = filterdf.R.tolist()
                        G_NG = filterdf.G.tolist()
                        B_NG = filterdf.B.tolist()
                        R_Yield_ls = filterdf.R_Yield.tolist()
                        G_Yield_ls = filterdf.G_Yield.tolist()
                        B_Yield_ls = filterdf.B_Yield.tolist()
                        xticks = filterdf.SHEET_ID.tolist()
                        MB_Yield = filterdf.Avg_Process_Yield.tolist()
                        table_and_fig_gap = self.table_and_fig_gap

                        for i in xticks:
                            if len(i) > 6:
                                table_and_fig_gap = -0.8
                                break

                        self.plotTable(
                            R_NG, G_NG, B_NG, R_Yield_ls, G_Yield_ls, B_Yield_ls, MB_Yield,
                            figName = f"{FullOPID}_{datetime.today().weekday()}_{figname_type}.jpg",
                            filterSheetdf = filterdf,
                            columnName1 = 'Avg_Process_Yield',
                            columnName2 = 'R',
                            columnName3 = 'G',
                            columnName4 = 'B',
                            columnName5 = 'Avg_No_Process_Yield',
                            xticks = xticks,
                            xticks2= every_date,
                            figTitle = f'{Model_type}" {FullOPID} Yield Trend Chart {lastweek[4:-2]}~{now_date[4:-2]}',
                            xticksRotation = 0,
                            RGBlabel = None,
                            rowLabels = ['R_NG', 'G_NG', 'B_NG', 'R_Yield', 'G_Yield', 'B_Yield', 'MB_Yield'],
                            table_bbox = [0, table_and_fig_gap, 1, 0.4],
                            bar_label_rotation = 0,
                            OPID=OPID
                        )
                else:
                    filterdf = res[res['OPID']==OPID].reset_index(drop=True)
                    filterdf = self.NMB_pivot_df(
                        'CreateTime', 'SHEET_ID', 'Total_CNT', 
                        filterSheetdf=filterdf, 
                        set_values='NGCNT',  # indicated R, G, B
                        set_index_column=True,
                        plot_report=True
                    )
                    filterdf = filterdf.drop(['Total_CNT','G_x','B_x','R_x','G_y','B_y','R_y'],  axis=1)
                    df_ls.append(filterdf)

                    FullOPID = self.OPID_comparison_table.get(OPID, None)
                    if len(filterdf.index)==0:
                        continue
                    else:
                        every_date = [str(i)[4:-2] for i in filterdf.CreateTime.tolist()]
                        R_NG = filterdf.R.tolist()
                        G_NG = filterdf.G.tolist()
                        B_NG = filterdf.B.tolist()
                        # PNG = filterdf.Process_NG.tolist()
                        R_Yield_ls = filterdf.R_Yield.tolist()
                        G_Yield_ls = filterdf.G_Yield.tolist()
                        B_Yield_ks = filterdf.B_Yield.tolist()
                        xticks = filterdf.SHEET_ID.tolist()
                        table_and_fig_gap = self.table_and_fig_gap

                        for i in xticks:
                            if len(i) > 6:
                                table_and_fig_gap = -0.8
                                break

                        self.plotTable(
                            R_NG, G_NG, B_NG, R_Yield_ls, G_Yield_ls, B_Yield_ks,
                            figName = f"{FullOPID}_{datetime.today().weekday()}_{figname_type}.jpg",
                            filterSheetdf = filterdf,
                            columnName1 = 'Avg_Process_Yield',
                            columnName2 = 'R',
                            columnName3 = 'G',
                            columnName4 = 'B',
                            columnName5 = 'Avg_No_Process_Yield',
                            xticks = filterdf.SHEET_ID.tolist(),
                            xticks2 = every_date,
                            figTitle = f'{Model_type}" {FullOPID} Yield Trend Chart {lastweek[4:-2]}~{now_date[4:-2]}',
                            xticksRotation = 0,
                            RGBlabel = None,
                            rowLabels = ['R_NG', 'G_NG', 'B_NG', 'R_Yield', 'G_Yield', 'B_Yield'],
                            table_bbox = [0, table_and_fig_gap, 1, 0.4],
                            bar_label_rotation = 0,
                            OPID=OPID
                        )
            temp_df = pd.concat(df_ls)
            pd.DataFrame.to_csv(temp_df, './report_production/TempDateFrame.csv')    
        else:
            logging.warning(f'No data from {lastweek} to {now_date}')
        return res


    def set_ylim_Using_standard_deviation(self, list1:list):
        ymin = 0
        arr = np.asarray(list1)
        if len(arr)==1:
            ymin = 0
            # print(ymin, ymax)
        else:   
            arr_std = arr.std(axis=0)
            arr_std = float(Decimal(arr_std).quantize(Decimal('.00'), ROUND_HALF_UP))
            # print(arr_std)
            arr_max = arr.max()
            arr_min = arr.min()
            if arr_std <= 0.5:
                ymin = arr_min - 20*(arr_std)
            if arr_std >= 1:
                ymin = arr_min - 1.05*(arr_max-arr_min)
            if ymin < 0:
                ymin =0 
             
        return int(ymin)


    def plotTable(self, *args, figName: str, filterSheetdf: pd.DataFrame, columnName1: str, 
                  columnName2: str, columnName3: str, columnName4: str, xticks=None, xticks2=None, xlabel=None, **kwargs):
        """The agrs is corresponding to celltext, each columnName will be created to a dataframe and plot the line or bar chart.

        The columnNames will be use like: 

                filterSheetdf[[columnName1]].plot(kind='line', marker='o', color ='tan', ylim=(0,140), ax=ax1, legend=False)

                filterSheetdf[[columnName2]].plot(kind='line', marker='d', color ='salmon', ylim=(0,120), ax=ax2, legend=False)
        
                filterSheetdf[[columnName3, columnName4]].plot(kind='bar', stacked=True, ylim=(0, NGheight), ax=ax3, legend=False)

        xticks should be a empty list or text list

        **kwargs:
                figTitle: str
                xlabelRotation: int
                RGBlabel: list | None
                bar_label_rotation: int

                ---Matplotlib table's params is as shown below---

                rowLabels: list
                colLabels: list | None
                table_bbox: list
                
        """
        colors = [self.R_color, self.G_color, self.B_color]
        
        if kwargs.get('OPID', None) == 'TNLBO':
            if len(xticks) < 16:
                fig, ax1 = plt.subplots(figsize=(10, 5))
            else:
                fig, ax1 = plt.subplots(figsize=(22, 5))
            
            ymin = self.set_ylim_Using_standard_deviation(filterSheetdf[columnName1].values.tolist())

            ax1.set_zorder(2)
            ax1.set_facecolor('none')
            ax2 = ax1.twinx()
            ax2.set_zorder(1) 
            ax2.set_facecolor('none')
            ax3 = ax1.twinx()
            ax3.set_zorder(3) 
            ax3.set_facecolor('none')
            ax3.set_visible(False)
            
            filterSheetdf[[columnName1]].plot(kind='line', marker='o', color ='black', ylim=(ymin, 100), ax=ax1, legend=False)
            filterSheetdf[[columnName2, columnName3, columnName4]].plot(kind='bar', stacked=False, color=colors, ax=ax2, ylim=(0, 400), legend=False)
            filterSheetdf['target'] = 99.8
            filterSheetdf['target'].plot(kind='line', color ='red', ylim=(ymin, 100), ax=ax1, legend=False)
            
            # ax1.set_xticklabels(filterSheetdf.SHEET_ID.tolist(), rotation=0)

            figTitle = kwargs.get('figTitle', 'Sample')
            
            
            if xlabel != None:
                ax1.set_xlabel(xlabel, fontsize=14)
            ax1.set_ylabel('Yiled', fontsize=14)

            rot = kwargs.get('xticksRotation', 0)
            sheet_date_labels = []
            if xticks != None and rot != None:
                for i in range(len(xticks)):
                    total = xticks2[i] + '\n\n' + xticks[i]
                    sheet_date_labels.append(total)
                # print(sheet_date_labels)
                ax1.set_xticklabels(sheet_date_labels, rotation = rot)
                

            ax2.set_title(f"{figTitle}", fontsize=20, pad=60)
            ax2.set_ylabel("NG_COUNT", fontsize=14)
            for xtick, y in zip(filterSheetdf.index, filterSheetdf['Avg_Process_Yield'].tolist()):
                if y == 0:
                    continue
                ax1.text(x=xtick, y=y+0.02, s=f'{y:.2f}%', ha="center", va='bottom', fontsize=8, rotation=0)
            
            the_table = ax1.table(
                cellText = args,
                rowLabels = kwargs.get('rowLabels'),
                colLabels = kwargs.get('colLabels', None),
                cellLoc='center',
                rowColours =['white']*len(kwargs.get('rowLabels')),
                bbox = kwargs.get('table_bbox'),
            )

            table_props = the_table.properties()
            table_cells = table_props['children']
            
            for cell in table_cells: 
                cell.get_text().set_color(self.color_dict.get(cell.get_text().get_text(), 'black'))

            labels = ['MB Yield', 'Target', 'R_NG', 'G_NG', 'B_NG']
            the_table.auto_set_font_size(False)
            the_table.set_fontsize(8)
            fig.legend(loc='upper center', labels=labels, bbox_to_anchor=(0.5, 1), ncol=len(labels), edgecolor='black')
            plt.savefig(f'{self.reportImgPath + figName}', bbox_inches='tight', dpi=500)
            plt.cla()
            plt.close(fig)
     

        else: 
            if len(xticks) < 10:
                fig, ax1 = plt.subplots(figsize=(10, 5))
            else:
                fig, ax1 = plt.subplots(figsize=(22, 5))
            ax1.set_zorder(2)
            ax1.set_facecolor('none')
            ax2 = ax1.twinx()
            ax2.set_zorder(1) 
            ax2.set_facecolor('none')
            ax3 = ax1.twinx()
            ax3.set_zorder(0)
            ax3.set_facecolor('none')

            ymin = self.set_ylim_Using_standard_deviation(list(filterSheetdf[columnName1]))

            filterSheetdf[[columnName1]].plot(kind='line', marker='o', color ='black', ylim=(ymin, 110), ax=ax1, legend=False)
            filterSheetdf[[kwargs.get('columnName5')]].plot(kind='line', marker='o', color ='saddlebrown', ylim=(0,120), ax=ax2, legend=False)
            filterSheetdf[[columnName2, columnName3, columnName4]].plot(kind='bar', stacked=False ,ylim=(0,400), color=colors, ax=ax3, legend=False)  
            filterSheetdf['target'] = 99.8

            figTitle = kwargs.get('figTitle', 'Sample')
            
            if xlabel != None:
                ax1.set_xlabel(xlabel, fontsize=14)
            ax1.set_ylabel('Bond_OK_Yield', fontsize=14)
            rot = kwargs.get('xticksRotation', 0)

            sheet_date_labels = []
            if xticks != None and rot != None:
                for i in range(len(xticks)):
                    total = xticks2[i] + '\n\n' + xticks[i]
                    sheet_date_labels.append(total)
                # print(sheet_date_labels)
                ax1.set_xticklabels(sheet_date_labels, rotation = rot)
      
            ax2.set_title(f"{figTitle}", fontsize=20, pad=60)
            ax2.spines['left'].set_position(('axes', -0.1))
            ax2.set_ylabel('No_Bond_OK_Yield', fontsize=14)
            ax2.yaxis.set_label_position("left")
            ax2.spines["left"].set_visible(True)
            ax2.yaxis.tick_left()

            ax3.set_ylabel("NG_COUNT", fontsize=14)

            for xtick, y in zip(filterSheetdf.index, filterSheetdf[columnName1].tolist()):
                if y == 0:
                    continue
                ax1.text(x=xtick, y=y+0.05, s=f'{y:.2f}%', ha="center", va='bottom', fontsize=8, rotation=0)

            for xtick, y in zip(filterSheetdf.index, filterSheetdf[kwargs.get('columnName5')].tolist()):
                if y == 0:
                    continue
                ax2.text(x=xtick, y=y+0.05, s=f'{y:.2f}%', ha="center", va='bottom', fontsize=8, rotation=0)

            the_table = ax1.table(
                cellText = args,
                rowLabels = kwargs.get('rowLabels'),
                colLabels = kwargs.get('colLabels', None),
                cellLoc='center',
                rowColours =['white']*len(kwargs.get('rowLabels')),
                bbox = kwargs.get('table_bbox'),
            )


            labels = ['Bond_OK_Yield', 'No_Bond_OK_Yield', 'R_NG', 'G_NG', 'B_NG']
            the_table.auto_set_font_size(False)
            the_table.set_fontsize(8)

            table_props = the_table.properties()
            table_cells = table_props['children']
            for cell in table_cells: 
                cell.get_text().set_color(self.color_dict.get(cell.get_text().get_text(), 'black'))

            fig.legend(loc='upper center', labels=labels, bbox_to_anchor=(0.5, 1), ncol=len(labels), edgecolor='black')
            plt.savefig(f'{self.reportImgPath + figName}', bbox_inches='tight', dpi=500)
            plt.cla()
            plt.close(fig)
        
    def clear_old_data(self):
        if not os.path.exists(self.reportImgPath):
            os.mkdir(self.reportImgPath)
        else:
            shutil.rmtree(self.reportImgPath)
            time.sleep(5)
            os.mkdir(self.reportImgPath)

    def read_summary_df(self): 
        if os.path.exists(self.summaryTablePath):
            Summary_df = self.readFile(self.summaryTablePath, MODEL=13.6) 
        else:
            message = 'File Not found SummaryTable.csv'
            customMessageAutoMail().send(message)
        return Summary_df



class ScatterStacked(TableType):
    def __init__(self):
        super(ScatterStacked, self).__init__()
        self.vertical_param = 0.1
        self.Horizontal_param = 0.1

    def removeFalseDefect(self, df, OPID):
        """Remove vertical & Horizontal false defect line.

        And keep the point of defect coordinate belong to process ng.
        """
        
        if OPID != "TNLBO":
            # remove vertical line
            for i in range(len(df.columns.tolist())):
                if (np.count_nonzero(df[i]==0) / len(df.index)) > self.vertical_param:
                    df[i] = np.where((df[i]==0) | (df[i]==1), 1, df[i]) 
                    

            # remove Horizontal line
            df = np.asarray(df, dtype='uint8') 
            for j in range(df.shape[0]):
                if (np.count_nonzero(df[j]==0) / df.shape[1]) > self.Horizontal_param:
                    df[j] = np.where((df[j]==0) | (df[j]==1), 1, df[j])

        else:
            for i in range(len(df.columns.tolist())):
                if (np.count_nonzero(df[i]==10) / len(df.index)) > self.vertical_param:
                    df[i] = np.where((df[i]==10), 11, 1) 

            df = np.asarray(df, dtype='uint8') 
            for j in range(df.shape[0]):
                if (np.count_nonzero(df[j]==10) / df.shape[1]) > self.Horizontal_param:
                    df[j] = np.where((df[j]==10), 11, 1)

        return df

    def changeMaximumValue(self, df):
        """
        If the dataframe dose not have corresponding bonding data, the max value will be 1.

        Because of the reason, the dataframe need to be change the max value to 11.
        """
        arr = np.asarray(df, dtype='uint8')
        max_value = arr.max()
        if max_value==1:
            new_df = np.where(df==1, 11, 10)
            new_df = pd.DataFrame(new_df)
        return new_df
    
    def ProduceScatterPlot(self, df, chooseTpye: str):
        if chooseTpye.lower() == 'daily':
            _, _, filterSheetdf = self.by24hours(df)
        if chooseTpye.lower() == 'weekly':
            _, _, filterSheetdf = self.byDays(df)

        if len(filterSheetdf.index) != 0:
            OPID_ls = set(filterSheetdf.OPID.tolist())
            sheetID_ls = set(filterSheetdf.SHEET_ID.tolist())
            for OPID in OPID_ls:
                OPID_df = filterSheetdf[(filterSheetdf['OPID']==OPID)].reset_index(drop=True)
                for sheet in sheetID_ls:
                    filterdf = OPID_df[(OPID_df['SHEET_ID']==sheet)].reset_index(drop=True)
                    if len(filterdf.index) == 0:
                        continue
                    else:
                        if OPID == 'TNLBO':
                            pivot_df = self.NMB_pivot_df(
                                'CreateTime', 'SHEET_ID', 'Total_CNT', 
                                filterSheetdf=filterdf, 
                                set_values='NGCNT', 
                                set_index_column=False
                            )
                            # stacked scatter plot
                            pivot_df = pivot_df.drop(['Avg_Process_Yield'],  axis=1)
                            FullOPID = self.OPID_comparison_table.get(OPID)
                            figname = f'{sheet}_{FullOPID}_Defect_MAP'
                            R_OPID_df = filterdf[filterdf['LED_TYPE']=='R'].reset_index(drop=True)
                            G_OPID_df = filterdf[filterdf['LED_TYPE']=='G'].reset_index(drop=True)
                            B_OPID_df = filterdf[filterdf['LED_TYPE']=='B'].reset_index(drop=True)
                            R_Yield = pd.read_csv(R_OPID_df.iloc[0].YiledAnalysis_2D)
                            G_Yield = pd.read_csv(G_OPID_df.iloc[0].YiledAnalysis_2D)
                            B_Yield = pd.read_csv(B_OPID_df.iloc[0].YiledAnalysis_2D)

                            # for table
                            date = [str(i)[4:-4] for i in pivot_df.CreateTime.tolist()]
                            R_NG = pivot_df.R.tolist()
                            G_NG = pivot_df.G.tolist()
                            B_NG = pivot_df.B.tolist()
                            R_Yield_ls = pivot_df.R_Yield.tolist()
                            G_Yield_ls = pivot_df.G_Yield.tolist()
                            B_Yield_ls = pivot_df.B_Yield.tolist()

                        else:
                            filterdf = OPID_df[(OPID_df['SHEET_ID']==sheet)].reset_index(drop=True)
                            pivot_df = self.NMB_pivot_df(
                                'CreateTime', 'SHEET_ID', 'Total_CNT',
                                filterSheetdf=filterdf, 
                                set_values='NGCNT', 
                                set_index_column=True
                            )
                            
                            # stacked scatter plot
                            # pivot_df = pivot_df.drop(['Avg_No_Process_Yield'],  axis=1)
                            FullOPID = self.OPID_comparison_table.get(OPID)
                            figname = f'{sheet}_{FullOPID}_Defect_MAP'
                            R_OPID_df = OPID_df[OPID_df['LED_TYPE']=='R'].reset_index(drop=True)
                            G_OPID_df = OPID_df[OPID_df['LED_TYPE']=='G'].reset_index(drop=True)
                            B_OPID_df = OPID_df[OPID_df['LED_TYPE']=='B'].reset_index(drop=True)
                            R_Yield = pd.read_csv(R_OPID_df.iloc[0].YiledAnalysis_2D)
                            G_Yield = pd.read_csv(G_OPID_df.iloc[0].YiledAnalysis_2D)
                            B_Yield = pd.read_csv(B_OPID_df.iloc[0].YiledAnalysis_2D)

                            # for table
                            # print(pivot_df)
                            date = [str(i)[4:-4] for i in pivot_df.CreateTime.tolist()]
                            R_NG = pivot_df.R.tolist()
                            G_NG = pivot_df.G.tolist()
                            B_NG = pivot_df.B.tolist()
                            R_Yield_ls = pivot_df.R_Yield.tolist()
                            G_Yield_ls = pivot_df.G_Yield.tolist()
                            B_Yield_ls = pivot_df.B_Yield.tolist()

                        if OPID=='TNLBO':
                            R_Yield = self.changeMaximumValue(R_Yield)
                            G_Yield = self.changeMaximumValue(G_Yield)
                            B_Yield = self.changeMaximumValue(B_Yield)

                        rowLabels = ['Date','R_NG', 'G_NG', 'B_NG', 'R_Yield', 'G_Yield', 'B_Yield']
                        # remove false defect
                        self.StackScatterPlot(
                            sheet, 
                            FullOPID, 
                            R_Yield, 
                            G_Yield, 
                            B_Yield, 
                            date, R_NG, G_NG, B_NG, R_Yield_ls, G_Yield_ls, B_Yield_ls,
                            removeFalseDefect=True, 
                            figname=figname, 
                            OPID=OPID,
                            rowLabels = rowLabels,
                            table_bbox = [1.1, 0, 0.15, 0.4]
                        )

                        self.StackScatterPlot(
                            sheet, 
                            FullOPID, 
                            R_Yield, 
                            G_Yield, 
                            B_Yield, 
                            date, R_NG, G_NG, B_NG, R_Yield_ls, G_Yield_ls, B_Yield_ls,
                            removeFalseDefect=False, 
                            figname=figname, 
                            OPID=OPID,
                            rowLabels = rowLabels,
                            table_bbox = [1.1, 0, 0.15, 0.4]
                        )
    
    def StackScatterPlot(self, sheetID:str, FullOPID:str, R_Yield:pd.DataFrame, G_Yield:pd.DataFrame, B_Yield:pd.
                         DataFrame, *args, removeFalseDefect:bool, **kwargs):
        """Stacked scatter is plotted following sheet ID that is the x axis of  the daily report.
    
        **kwargs:

            figname
            OPID
        """
        xymin = -25
        xmax = 525
        ymax = 295

        R_Yield.columns = R_Yield.columns.astype('int')
        G_Yield.columns = G_Yield.columns.astype('int')
        B_Yield.columns = B_Yield.columns.astype('int')

        OPID = kwargs.get('OPID')
        if OPID =='TNLBO':
            if removeFalseDefect == True:
                R_Yield = self.removeFalseDefect(R_Yield, OPID)
                G_Yield = self.removeFalseDefect(G_Yield, OPID)
                B_Yield = self.removeFalseDefect(B_Yield, OPID)

                RPNG = np.where(R_Yield == 10) # coordinate
                GPNG = np.where(G_Yield == 10) # coordinate
                BPNG = np.where(B_Yield == 10) # coordinate
            else:
                RPNG = np.where(R_Yield == 10) # coordinate
                GPNG = np.where(G_Yield == 10) # coordinate
                BPNG = np.where(B_Yield == 10)
        else:
            if removeFalseDefect == True:
                R_Yield = self.removeFalseDefect(R_Yield, OPID)
                G_Yield = self.removeFalseDefect(G_Yield, OPID)
                B_Yield = self.removeFalseDefect(B_Yield, OPID)

                RPNG = np.where(R_Yield == 10) # coordinate
                RPOK = np.where(R_Yield == 11)
                RNPNG = np.where(R_Yield == 0)
                
                GPNG = np.where(G_Yield == 10) # coordinate
                GPOK = np.where(G_Yield == 11)
                GNPNG = np.where(G_Yield == 0)
                
                BPNG = np.where(B_Yield == 10) # coordinate
                BPOK = np.where(B_Yield == 11)
                BNPNG = np.where(B_Yield == 0)   
            else:
                RPNG = np.where(R_Yield == 10) # coordinate
                RPOK = np.where(R_Yield == 11)
                RNPNG = np.where(R_Yield == 0)

                GPNG = np.where(G_Yield == 10) # coordinate
                GPOK = np.where(G_Yield == 11)
                GNPNG = np.where(G_Yield == 0)

                BPNG = np.where(B_Yield == 10) # coordinate
                BPOK = np.where(B_Yield == 11)
                BNPNG = np.where(B_Yield == 0)

        fig, ax = plt.subplots(figsize=(10, 5))
        
        ax.grid()
        ax.set_zorder(2)
        ax2, ax3, ax4, ax5, ax6, ax7, ax8, ax9 = ax.twinx(), ax.twinx(), ax.twinx(), ax.twinx(), ax.twinx(), ax.twinx(), ax.twinx(), ax.twinx()
        ax2.set_zorder(0) 
        ax3.set_zorder(2)
        ax4.set_zorder(0)
        ax5.set_zorder(2)
        ax6.set_zorder(0)
        ax7.set_zorder(2)
        ax8.set_zorder(2)
        ax9.set_zorder(2)

        ax.set_title(f"{sheetID}_{FullOPID} RGB Defect Map")
        ax.set_facecolor('none')
        ax2.set_facecolor('none')
        ax3.set_facecolor('none')
        ax4.set_facecolor('none')
        ax5.set_facecolor('none')
        ax6.set_facecolor('none')
        ax7.set_facecolor('none')
        ax8.set_facecolor('none')
        ax9.set_facecolor('none')

        ax2.set_yticklabels([])
        ax3.set_yticklabels([])
        ax4.set_yticklabels([])
        ax5.set_yticklabels([])
        ax6.set_yticklabels([])
        ax7.set_yticklabels([])
        ax8.set_yticklabels([])
        ax9.set_yticklabels([])

        ax.set_xlim([xymin, xmax])
        ax.set_ylim([xymin, ymax])
        ax2.set_ylim([xymin, ymax])
        ax3.set_ylim([xymin, ymax])
        ax4.set_ylim([xymin, ymax])
        ax5.set_ylim([xymin, ymax])
        ax6.set_ylim([xymin, ymax])
        ax7.set_ylim([xymin, ymax])
        ax8.set_ylim([xymin, ymax])
        ax9.set_ylim([xymin, ymax])



        if OPID == 'TNLBO':
            labels = ['R_Process_NG', 'G_Process_NG', 'B_Process_NG']
            ax.scatter(list(RPNG[1]), list(RPNG[0]), s=200, marker='.', edgecolors='lightcoral', facecolors='none')
            ax2.scatter(list(GPNG[1]), list(GPNG[0]), s=100, marker='.', edgecolors='forestgreen', facecolors='none')
            ax3.scatter(list(BPNG[1]), list(BPNG[0]), s=50, marker='.', edgecolors='dodgerblue', facecolors='none')
            ax.invert_yaxis()
            ax2.invert_yaxis()
            ax3.invert_yaxis()
            the_table = ax.table(
                cellText = args,
                rowLabels = kwargs.get('rowLabels'),
                colLabels = kwargs.get('colLabels', None),
                cellLoc='center',
                rowColours =['white']*len(kwargs.get('rowLabels')),
                bbox = kwargs.get('table_bbox'),
            )
            the_table.auto_set_font_size(False)
            the_table.set_fontsize(8)
            table_props = the_table.properties()
            table_cells = table_props['children']
            for cell in table_cells: 
                cell.get_text().set_color(self.color_dict.get(cell.get_text().get_text(), 'black'))
            fig.legend(loc='upper left', labels=labels, bbox_to_anchor=(0.93, -0.1, 1, 1), edgecolor='black')
            

        else:
            ax.scatter(list(RPNG[1]), list(RPNG[0]), s=150, marker='D', edgecolors='lightcoral', facecolors='none')
            ax2.scatter(list(RNPNG[1]), list(RNPNG[0]), s=150, marker='.', edgecolors='red', facecolors='none')
            ax3.scatter(list(RPOK[1]), list(RPOK[0]), s=150, marker='*', edgecolors='brown', facecolors='none')
            ax4.scatter(list(GPNG[1]), list(GPNG[0]), s=100, marker='D', edgecolors='forestgreen', facecolors='none')
            ax5.scatter(list(GNPNG[1]), list(GNPNG[0]), s=100, marker='.', edgecolors='green', facecolors='none')
            ax6.scatter(list(GPOK[1]), list(GPOK[0]), s=100, marker='*', edgecolors='lime', facecolors='none')
            ax7.scatter(list(BPNG[1]), list(BPNG[0]), s=50, marker='D', edgecolors='dodgerblue', facecolors='none')
            ax8.scatter(list(BNPNG[1]), list(BNPNG[0]), s=50, marker='.', edgecolors='blue', facecolors='none')
            ax9.scatter(list(BPOK[1]), list(BPOK[0]), s=50, marker='*', edgecolors='royalblue', facecolors='none')

            ax.invert_yaxis()
            ax2.invert_yaxis()
            ax3.invert_yaxis()
            ax4.invert_yaxis()
            ax5.invert_yaxis()
            ax6.invert_yaxis()
            ax7.invert_yaxis()
            ax8.invert_yaxis()
            ax9.invert_yaxis()
            the_table = ax.table(
                cellText = args,
                rowLabels = kwargs.get('rowLabels'),
                colLabels = kwargs.get('colLabels', None),
                cellLoc='center',
                rowColours =['white']*len(kwargs.get('rowLabels')),
                bbox = kwargs.get('table_bbox'),
            )
            the_table.auto_set_font_size(False)
            the_table.set_fontsize(8)
            table_props = the_table.properties()
            table_cells = table_props['children']
            for cell in table_cells: 
                cell.get_text().set_color(self.color_dict.get(cell.get_text().get_text(), 'black'))
            fig.legend(loc='upper left', labels=self.labels, bbox_to_anchor=(0.93, -0.1, 1, 1), edgecolor='black')
            
        figname = kwargs.get('figname')

        if removeFalseDefect==True:
            plt.savefig(f'{self.reportImgPath + figname}_rmDefect.png', bbox_inches='tight', dpi=500)
        else:
            plt.savefig(f'{self.reportImgPath + figname}_original.png', bbox_inches='tight', dpi=500)

        plt.cla()
        plt.close(fig)
       
def plot24Hours():
    """
    Every day, the save folder will be cleaned and create a new file.
    """
    choose = TableType()
    scatterPlot = ScatterStacked()
    choose.clear_old_data()
    if os.path.exists(choose.summaryTablePath):
        # try:
        Summary_df = choose.read_summary_df()
        filterDF = choose.ChooseReportType(Summary_df, Model_type=13.55, choose_report_type='daily')
        sheetID_ls = set(filterDF.SHEET_ID.tolist())
        # getLightOnResult(sheetID_ls)
        # scatterPlot.ProduceScatterPlot(Summary_df, chooseTpye='daily')
            # pptx_name = PPTmain().dailyReport()
        #     auto_mail().sendReport(choose.reportImgPath + 'TempDateFrame.csv', messageForTableType='Daily')
        # except Exception as E:
        #     logging.warning(f'plot24Hours warning: {E}')

def plotDay():
    choose = TableType()
    scatterPlot = ScatterStacked()
    choose.clear_old_data()
    if os.path.exists(choose.summaryTablePath):
        try:
            Summary_df = choose.read_summary_df()
            filterDF = choose.ChooseReportType(Summary_df, Model_type=13.55, choose_report_type='weekly')
            sheetID_ls = set(filterDF.SHEET_ID.tolist())
            getLightOnResult(sheetID_ls)
            scatterPlot.ProduceScatterPlot(Summary_df, chooseTpye='weekly')
            pptx_name = PPTmain().weeklyReport()
            auto_mail().sendReport(choose.reportImgPath + 'TempDateFrame.csv', messageForTableType='Weekly')
        except Exception as E:
            logging.warning(f'plotDay warning: {E}')

if __name__ == '__main__':
    
    # schedule.every().days.at("07:30").do(plot24Hours)
    # schedule.every().wednesday.at("07:35").do(plotDay)

    # plotHours()
    plot24Hours()
    # plotDay()

    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
        
        

