import pandas as pd

# df = pd.read_csv(r"C:\Users\iq750\Downloads\서울시 상권분석서비스(상주인구-상권).csv", encoding = 'euc-kr')
# print(df.columns)
# print(len(df))
# print(df.value_counts('기준_년분기_코드').sort_index(ascending=True))
# 상주인구 사용 유효
df = pd.read_csv(r"C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\Yesha\ERD\서울시 상권분석서비스(상주인구-상권).csv", encoding = 'euc-kr')
# print(df.columns)
print(len(df))
df_sang = df[df['상권_구분_코드_명'] == '발달상권']
print(df_sang[['기준_년분기_코드','상권_코드_명','남성_상주인구_수', '여성_상주인구_수']].sort_values(by='기준_년분기_코드', ascending=False).head(10))
