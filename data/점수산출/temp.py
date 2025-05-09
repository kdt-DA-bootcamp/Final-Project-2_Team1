import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 한글 폰트 설정
font_path = r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\fonts\강원교육모두 Light.ttf'
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False

df_cafes = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\카페_상권_매핑_데이터_중복제거.csv')

df_sales = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정매출결과_0509.csv')
#print('매출 분석 결과:\n',df_sales.describe())
df_cost = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\임대료_추정_최종_0509.csv')

# print('임대료 분석 결과:\n', df_cost.describe())
['상가업소번호', '상호명_지점', '상권_코드', '전용면적', '리뷰수', '별점', '카페_추정매출']
df_sales['연매출'] = df_sales['카페_추정매출'] # 얘는 연매출이 맞음
print(df_sales[['상가업소번호','연매출']].sort_values(by = '상가업소번호').head(5))
['상가업소번호', '상호명', '도로명주소', '지점명', '시군구명', '상가유형', '행정동명_추정', '임대료_분류', '전용면적', '전용면적(평)', '평당임대료', '추정임대료(천원)']
df_cost["연임대료"] = df_cost["추정임대료(천원)"] * 12 * 1000
print(df_cost[['상가업소번호','연임대료']].sort_values(by = '상가업소번호').head(5))

df_cal = pd.merge(df_sales[['상가업소번호','상권_코드','연매출']], df_cost[['상가업소번호','연임대료']], on = '상가업소번호')
df_cal['매출_임대료_비율'] = df_cal['연매출'] /(1 +  df_cal['연임대료'])
df_cal['추정_순이익'] = df_cal['연매출'] - df_cal['연임대료']
df_cal.to_csv(
    r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정순익.csv',
    encoding = 'utf-8-sig', index = False)
print(df_cal['추정_순이익'].isna().sum())
