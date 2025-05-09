# 필요한 라이브러리
import pandas as pd

# 카페 점수화 방식에 맞게 전체 코드 정리하기
# 기존 점수 파일
df_score = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0503.csv')
print(df_score.columns.tolist())
# 기간, 주차장, 층수는 미리 정리
df_score = df_score[['상가업소번호','TRDAR_CD', 'period_score','parking_score','floor_score']]

##################################################################
# 매출 5분위로 나누어서 점수 부여 (없는 곳 처리 방법 포함)
df_sales = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정매출결과_0509.csv')
def assign_grouped_review_score(df, group_col, value_col):
    def score_within_group(group):
        score = pd.Series(index=group.index, dtype='float')

        # 0점 처리
        score[group[value_col] == 0] = 0

        # 0 초과 & notna인 값만 추출
        valid_mask = (group[value_col] > 0) & (group[value_col].notna())
        valid_values = group.loc[valid_mask, value_col]

        if len(valid_values) >= 5:
            try:
                # 분위수 계산 시 중복 구간 제거
                quantiles = pd.qcut(valid_values, q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
                score[valid_mask] = quantiles.astype(int)
            except ValueError:
                # 값이 모두 동일해서 실패하면 3점 부여
                score[valid_mask] = 3
        else:
            score[valid_mask] = 3

        return score

    return df.groupby(group_col).apply(score_within_group, include_groups=False).reset_index(level=0, drop=True)
df_sales['카페_추정매출'] = pd.to_numeric(df_sales['카페_추정매출'], errors='coerce')

df_sales['sales_score_grouped'] = assign_grouped_review_score(
    df_sales,
    group_col='상권_코드',
    value_col='카페_추정매출'
)
# Nan 값 채우는 코드
df_sales['sales_score_grouped'] = df_sales['sales_score_grouped'].fillna(3)
df_score = df_score.merge(df_sales[['상가업소번호','sales_score_grouped']], on = '상가업소번호',how = 'left')
##################################################################
df_review = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_별점리뷰통합.csv')
# 리뷰 수 (5분위)
df_review['naver_reviewCount'] = pd.to_numeric(df_review['naver_reviewCount'], errors='coerce')
df_review['kakao_reviewCount'] = pd.to_numeric(df_review['kakao_reviewCount'], errors='coerce')
df_review['sum_reviewCount'] = df_review[['naver_reviewCount', 'kakao_reviewCount']].sum(axis=1, skipna=True)

# 점수 계산 함수
def assign_review_score(series):
    # 0인 항목은 0점
    score = pd.Series(0, index=series.index)

    # 0 초과 & notna 값만 대상으로 분위수 기반 점수 부여
    valid_mask = (series > 0) & (series.notna())
    valid_series = series[valid_mask]

    # 분위수 기반 구간 나누기 (labels: 1~5, 높은 수치에 높은 점수)
    quantiles = pd.qcut(valid_series, q=5, labels=[1, 2, 3, 4, 5])

    # 결과 반영
    score[valid_mask] = quantiles.astype(int)
    return score

# 적용
df_review['5bin_review_score'] = assign_review_score(df_review['sum_reviewCount'])
# 평점 평균 (그대로, 소수점 1번째 자리까지 표현)

df_review['naver_score'] = df_review['naver_score'].fillna(3)
df_review['kakao_score'] = df_review['kakao_score'].fillna(3)

# 3. 평균 평점 계산
def get_avg_rating(kakao, naver):
    if kakao > 0 and naver > 0:
        return (kakao + naver) / 2
    elif kakao > 0:
        return kakao
    elif naver > 0:
        return naver
    else:
        return 0

df_review['avg_score'] = df_review.apply(lambda row: get_avg_rating(row['kakao_score'], row['naver_score']), axis=1)

df_review['avg_score'].head(10)

df_review.rename(columns={'avg_score':'rating_score'}, inplace=True)

df_score = df_score.merge(df_review[['상가업소번호','rating_score','5bin_review_score']], how = 'left', on = '상가업소번호')
##################################################################
# 추정 임대료 (어떻게 처리할 것인지 고민해야 함)
# 추정 임대료를 통해 예상 순이익을 구함 -> 5분위
df_cost = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정순익.csv')
df_cost['추정_순이익'] = pd.to_numeric(df_cost['추정_순이익'], errors='coerce')

df_cost['profit_score_grouped'] = assign_grouped_review_score(
    df_cost,
    group_col='상권_코드',
    value_col='추정_순이익'
) 
df_cost['profit_score_grouped'] = df_cost['profit_score_grouped'].fillna(3)

df_score = df_score.merge(df_cost[['상가업소번호','profit_score_grouped']], on = '상가업소번호',how = 'left')

df_score.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0510.csv', encoding = 'utf-8-sig', index = False)

# 남은 과제 정리
"""
1. 매출 & 순익 다시 정리해 보기
2. 성공카페 라벨링 여러 개 시도해 보기
3. 상관관계 그나마 높은 것 하나 선정해서 정리 (앞으로 유사 매물 추천할 방식)
4. 모두 끝나면 반드시 노션에 정리!!!
"""