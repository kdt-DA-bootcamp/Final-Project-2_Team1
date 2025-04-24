import os
import pandas as pd

path = r'C:/Users/iq750/bootcamp_git/Final-Project-2_Team1/data/상가정보'
folder = os.listdir(path)
file_list = [os.path.join(path, f) for f in folder]
print(folder)
df_list = []
for file in file_list:
    print(f"Reading {file}...")
    for encoding in ['utf-8', 'euc-kr', 'cp949']:
        try:
            temp = pd.read_csv(file, encoding=encoding, dtype=str, low_memory=False)
            print(f"✅ Success with encoding: {encoding}")
            break
        except Exception as e:
            print(f"❌ Failed with encoding {encoding}: {e}")
    else:
        print(f"❌ All decoding attempts failed for {file}")
        continue

    # 서울시 카페만 필터링
    df = temp[(temp['시도명'] == '서울특별시') & (temp['상권업종소분류코드'] == 'I21201')]
    # 열 이름에 불필요한 공백 제거 및 수정
    df.columns = df.columns.str.replace(' ', '')  # 공백 제거
    df.columns = df.columns.str.replace('동정보', '동정보')  # 오타 수정
    df.columns = df.columns.str.replace('도 로명', '도로명')  # 공백 제거 및 통합
    df_list.append(df)
    
    # print(df.columns)

# 방법1: 마지막 파일 df_list[4]와 나머지를 하나씩 비교함
# .copy()를 사용하여 DataFrame 복사
df_recent = df_list[4].copy()
print(df_recent.columns)

# 'score' 컬럼을 추가하고 초기값을 1로 설정
df_recent['period_score'] = 1

# 3개월 이상 영업 (df_list[3])
df_recent.loc[df_recent['상가업소번호'].isin(df_list[3]['상가업소번호']), 'period_score'] = 2

# 6개월 이상 영업 (df_list[2])
df_recent.loc[df_recent['상가업소번호'].isin(df_list[2]['상가업소번호']), 'period_score'] = 3

# 1년 이상 영업 (df_list[1])
df_recent.loc[df_recent['상가업소번호'].isin(df_list[1]['상가업소번호']), 'period_score'] = 4

# 2년 이상 영업 (df_list[0])
df_recent.loc[df_recent['상가업소번호'].isin(df_list[0]['상가업소번호']), 'period_score'] = 5

# 결과 확인

print(df_recent['period_score'].value_counts())
print(df_recent[['상호명', 'period_score']].tail(10))

df_recent_save = df_recent[['상가업소번호','period_score']]
df_recent_save.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\카페_운영기간점수.csv', encoding = 'utf-8-sig', index = False)