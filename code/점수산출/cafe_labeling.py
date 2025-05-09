# 여러 가지 버전으로 라벨링 할 예정

# 그전에 매출 점수 붙이기
import pandas as pd

# 함수#####################
def assign_review_score(series):
    score = pd.Series(0, index=series.index)
    valid_mask = (series > 0) & (series.notna())
    valid_series = series[valid_mask]

    try:
        quantiles = pd.qcut(valid_series, q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
        score[valid_mask] = quantiles.astype(int)
    except ValueError:
        # 분위수 분할이 실패할 경우(예: 고유값이 적음) 전체를 3점으로 처리
        score[valid_mask] = 3

    return score
##########################

df_sales = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정매출결과_중복제거.csv')
# df_sales_columns = ['상가업소번호','상호명_지점','상권_코드','전용면적','리뷰수','별점','카페_추정매출']

df_sales = df_sales[['상가업소번호','카페_추정매출']]
# 상권코드 다시 매핑
df_area = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\카페_상권_매핑_데이터_중복제거.csv')
df_sales = df_sales.merge(df_area[['상가업소번호','TRDAR_CD']], how = 'left',on = '상가업소번호')
# 적용 : 상권별 0~5점 부여
df_sales['5bin_sales_score'] = 0  # 초기값

for area_code, group in df_sales.groupby('TRDAR_CD'):
    if len(group) < 5:
        # 매장이 5개 미만이면 review_score 3점 부여
        df_sales.loc[group.index, '5bin_sales_score'] = 3
    else:
        # 매장이 5개 이상이면 분위수 기반 점수 부여
        scores = assign_review_score(group['카페_추정매출'])
        df_sales.loc[group.index, '5bin_sales_score'] = scores
# print(df_sales.head(5))

df_score = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0503.csv')
df_score = df_score[['상가업소번호','period_score','floor_score','parking_score','5bin_review_score','minmax_review_score','rating_score']]
df_score = df_score.merge(df_sales[['상가업소번호','TRDAR_CD','5bin_sales_score']],how= 'left', on = '상가업소번호')
# print(df_score.columns.tolist())
df_score = df_score[['상가업소번호', 'period_score', 'floor_score', 'parking_score', '5bin_review_score', 'minmax_review_score', '5bin_sales_score', 'rating_score','TRDAR_CD']]
df_score['TRDAR_CD'] = df_score['TRDAR_CD'].fillna(-1).astype(int)
 # Nan 값제외하고 모두 정수로
df_score[['parking_score', 'floor_score']] = df_score[['parking_score', 'floor_score']].fillna(0)

print(df_score.head(4))
print("결측치 개수:\n", df_score.isna().sum().sort_values(ascending=False))

df_score.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0503.csv', encoding = 'utf-8-sig',index = False)