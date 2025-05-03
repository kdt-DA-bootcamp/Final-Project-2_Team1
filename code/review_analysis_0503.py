# 라이브러리
import pandas as pd
import numpy as np

# 불러와야 하는 데이터
df_review = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_별점리뷰통합.csv')
# 쉼표 제거 → 결측값 채우기 → 정수형 변환
df_review['kakao_reviewCount'] = df_review['kakao_reviewCount'].astype(str).str.replace(',', '').replace('nan', '0').astype(float).astype(int)
df_review['naver_reviewCount'] = df_review['naver_reviewCount'].astype(str).str.replace(',', '').replace('nan', '0').astype(float).astype(int)
df_period = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0502.csv')
df_review = df_review.merge(df_period[['상가업소번호', 'period_score']], how = 'left', on = '상가업소번호')

# 리뷰 수 정리 다시 하기
df_review['sum_review'] = df_review['kakao_reviewCount'] + df_review['naver_reviewCount']

# 전체 리뷰 수만 따지면 문제가 됨 (영업기간 점수로 나누어 조정)
df_review['sum_review'] = df_review['sum_review'] / df_review['period_score']

# 5bin은 상권별로 시행 (상권별 활성화 정도의 차이를 고려) - 매장이 5개 미만인 경우 고려해야 함
# 점수 계산 함수
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

# 상권 맵핑 필요
df_area = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\카페_상권_매핑_데이터_중복제거.csv')
df_area = df_area[['상가업소번호','TRDAR_CD']]
df_review = df_review.merge(df_area, on ='상가업소번호',how = 'left')

# 적용 : 상권별 0~5점 부여
df_review['5bin_review_score'] = 0  # 초기값

for area_code, group in df_review.groupby('TRDAR_CD'):
    if len(group) < 5:
        # 매장이 5개 미만이면 review_score 3점 부여
        df_review.loc[group.index, '5bin_review_score'] = 3
    else:
        # 매장이 5개 이상이면 분위수 기반 점수 부여
        scores = assign_review_score(group['sum_review'])
        df_review.loc[group.index, '5bin_review_score'] = scores

# 상권별 min-max 정규화 점수 계산
df_review['minmax_review_score'] = 0.0  # 초기화

for area_code, group in df_review.groupby('TRDAR_CD'):
    values = group['sum_review']
    min_val = values.min()
    max_val = values.max()
    
    # 모든 값이 동일한 경우 (max == min) 방지
    if max_val != min_val:
        normalized = (values - min_val) / (max_val - min_val)
    else:
        normalized = 0.0  # 동일값이면 모두 0 처리

    df_review.loc[group.index, 'minmax_review_score'] = normalized

df_new = pd.merge(df_period[['상가업소번호', 'period_score','floor_score','parking_score']], df_review[['상가업소번호','5bin_review_score','minmax_review_score']])
print(df_new.head(5))
df_new.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0503.csv', encoding = 'utf-8-sig', index = False)