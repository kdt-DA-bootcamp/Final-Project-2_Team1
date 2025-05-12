# 필요한 라이브러리
import pandas as pd
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
                quantiles = pd.qcut(valid_values, q=5, labels=[1, 2, 3, 4, 5], duplicates='raise')  # duplicates를 'raise'로 설정하여 오류 발생 시 확인
                score[valid_mask] = quantiles.astype(int)
            except ValueError:
                # 값이 모두 동일해서 실패하면 3점 부여
                score[valid_mask] = 3
        else:
            score[valid_mask] = 3

        return score

    return df.groupby(group_col).apply(score_within_group, include_groups=False).reset_index(level=0, drop=True)
# 카페 점수화 방식에 맞게 전체 코드 정리하기
# 기존 점수 파일
df_score = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0503.csv')
# print(df_score.columns.tolist())
# 기간, 주차장, 층수는 미리 정리
df_score = df_score[['상가업소번호','TRDAR_CD', 'period_score','parking_score','floor_score']]
print('처음 점수: ',len(df_score))

df_mapping = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\카페_상권_매핑_데이터_중복제거.csv')

df_cost = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정순익_0510.csv')
print(df_cost['추정_순이익'].isna().value_counts())

df_cost['추정_순이익'].describe()
df_cost_p = df_cost[df_cost['추정_순이익']>0]
print(len(df_cost_p))
# print(df_cost.columns)
df_cost['추정_순이익'] = pd.to_numeric(df_cost['추정_순이익'], errors='coerce')
# print(set(df_mapping['TRDAR_CD']) == set(df_cost['상권_코드'])) # True (맵핑에 이상 없음)
# print(set(df_score['상가업소번호']) == set(df_cost['상가업소번호'])) # True (완전 매핑 가능함)
# df_score에 있는 상가업소번호 중 df_cost에 존재하지 않는 항목 확인
missing_in_cost = df_score[~df_score['상가업소번호'].isin(df_cost['상가업소번호'])]
print("df_score에 있지만 df_cost에 없는 상가업소번호 개수:", len(missing_in_cost)) # 결과 0 (맵핑 가능함)
print("df_cost에서 상가업소번호 고유값 수:", df_cost['상가업소번호'].nunique())
print("df_cost 총 행 수:", len(df_cost))

# 함수 새로 수정할 것 
# df_cost의 데이터를 상권코드 별로 묶음 (여기에 결측치 웨 이렇게 많아요?)
# 상권 코드 내에서 5분위로 점수 부여
# 그 점수를 df_cost['profit_score_grouped'] 추가


# df_score = df_score.merge(df_cost[['상가업소번호','profit_score_grouped']], on = '상가업소번호',how = 'left')
# print('순익 추가 길이: ',len(df_score))
# print(df_score.head(6))
# print('점수의 결측치 개수\n',df_score.isna().sum())