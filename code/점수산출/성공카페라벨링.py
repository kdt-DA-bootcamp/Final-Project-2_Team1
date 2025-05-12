import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
# 한글 폰트 설정
font_path = r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\fonts\강원교육모두 Light.ttf'
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False

# 점수 불러오기
df = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_점수_0511.csv')
# print(len(df),'\n',df.isna().sum()) # sales and profit  
# print(df['상가업소번호'].value_counts())
before = len(df)
df.dropna(inplace=True)
after = len(df)
# sys.exit()
# 칼럼리스트
# 상가업소번호,TRDAR_CD,period_score,parking_score,floor_score,sales_score_grouped,rating_score,5bin_review_score,profit_score_grouped

score_list = ['period_score','parking_score','floor_score','sales_score_grouped','rating_score','5bin_review_score','profit_score_grouped']
# 모두 5점 척도로 정규화되어 있음

# 1. 어떤 기준으로 점수를 산출할 것인가?

#리뷰와 영업기간 높게, 매출은 조금 적게
# df['total_score'] = df[score_list].sum(axis=1)
df['total_score'] = df['period_score'] * 0.2 + df['rating_score'] * 0.3 + df['5bin_review_score'] * 0.3 + df['sales_score_grouped'] * 0.1 + df['profit_score_grouped'] * 0.1 + (df['parking_score'] * 0.2 + df['floor_score'] * 0.2) # 괄호는 보너스 스코어 (0 or 1)
# 2. 어떤 기준을 성공한 카페라고 할 수 있는가?
# 상위 30%
cutoff_70 = df['total_score'].quantile(0.7)
df['sucess']  = (df['total_score'] >= cutoff_70).astype(int)

sns.histplot(df['total_score'], bins=20, kde=True)
plt.title("가중치 합산 점수 분포_2")
plt.xlabel("총점")
plt.ylabel("카페 수")
plt.savefig(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\시각화\성공카페_점수분포_가중치2.png')
plt.show()

# 성공 카페와 매물 추천 feature들 간의 상관관계 파악하기
features = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\매물추천\카페_통합_최종데이터.csv')
add_feature = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정매출결과_0511.csv')
add_feature.dropna(inplace=True)
add_feature2 = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정순익_0511.csv')
add_feature2.dropna(inplace=True)
# print(features.columns.tolist())

# features에서 빼야 하는 것: 카페_추정매출
features = features.drop(columns=['카페_추정매출','전용면적','리뷰수','별점'])
features = features.merge(add_feature[['상가업소번호','균등분배_전용면적','리뷰수','별점','카페_추정매출']], on = '상가업소번호', how = 'left')
features = features.merge(add_feature2[['상가업소번호','매출_임대료_비율','추정_순이익']], on = "상가업소번호", how = 'left')

def convert_floor(floor):
    try:
        # B1, B2 등은 지하층을 의미하므로 음수로 변환
        if isinstance(floor, str) and floor.startswith('B'):
            return -int(floor[1:])
        else:
            return int(floor)
    except:
        return None  # 오류가 나는 경우는 결측치로 처리
features['층정보'] = features['층정보'].apply(convert_floor)
features_with_label = pd.merge(features, df[['상가업소번호','sucess']], how = 'left', on = '상가업소번호')
# 통합 데이터 수정해야 하는 부분: 추정_매출, + 추정 순이익 추가, 균등분배_전용면적
cols = [
 '층정보',
# '경도',
# '위도',
 '지하철역_거리(m)',
 '버스정류장_거리(m)',
 '반경500m내_카페수',
 '총_유동인구_수',
 '피크_유동인구_수_상권별',
 '피크_유동인구_수_11~14',
 '평균_평일_유동인구_수',
 '평균_주말_유동인구_수',
 '평일_대비_주말_유동인구_비율',
 '균등분배_전용면적',
 '리뷰수',
 '별점',
 '카페_추정매출',
 'sucess',
# 'TRDAR_CD',
 '매출_임대료_비율',
 '추정_순이익'
]

selected = features_with_label[cols].dropna()
correlation = selected.corr(numeric_only=True)['sucess'].sort_values(ascending=False)
print(correlation)
