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
before = len(df)
df.dropna(inplace=True)
after = len(df)

# 점수 리스트
score_list = ['period_score','parking_score','floor_score','sales_score_grouped','rating_score','5bin_review_score','profit_score_grouped']

# 가중치 기반 총점 계산
df['총점'] = (
    df['period_score'] * 0.2 +
    df['rating_score'] * 0.3 +
    df['5bin_review_score'] * 0.3 +
    df['sales_score_grouped'] * 0.1 +
    df['profit_score_grouped'] * 0.1 +
    (df['parking_score'] * 0.2 + df['floor_score'] * 0.2)  # 보너스 항목
)

# 3단계 분류 기준
cutoff_70 = df['총점'].quantile(0.7)
cutoff_40 = df['총점'].quantile(0.4)

def label_success(score):
    if score >= cutoff_70:
        return 2  # 성공
    elif score >= cutoff_40:
        return 1  # 보통
    else:
        return 0  # 실패

df['sucess'] = df['총점'].apply(label_success)

# 분포 저장 (선택)
sns.histplot(df['총점'], bins=20, kde=True)
plt.title("가중치 합산 점수 분포 (3단계)")
plt.xlabel("총점")
plt.ylabel("카페 수")
plt.savefig(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\시각화\성공카페_점수분포_다중.png')
plt.show()

# 저장
df.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_성공여부_다중.csv', encoding='utf-8-sig', index=False)
sys.exit()
# ---- 이하 피처 병합 및 전처리 ----

features = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\매물추천\카페_통합_최종데이터.csv')
add_feature = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정매출결과_0511.csv')
add_feature.dropna(inplace=True)
add_feature2 = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\점수산출\카페_추정순익_0511.csv')
add_feature2.dropna(inplace=True)

# 기존 값 제거 후 병합
features = features.drop(columns=['카페_추정매출','전용면적','리뷰수','별점'])
features = features.merge(add_feature[['상가업소번호','균등분배_전용면적','리뷰수','별점','카페_추정매출']], on='상가업소번호', how='left')
features = features.merge(add_feature2[['상가업소번호','매출_임대료_비율','추정_순이익']], on='상가업소번호', how='left')

# 층수 변환 함수
def convert_floor(floor):
    try:
        if isinstance(floor, str) and floor.startswith('B'):
            return -int(floor[1:])
        else:
            return int(floor)
    except:
        return None

features['층정보'] = features['층정보'].apply(convert_floor)

# 라벨 병합
features_with_label = pd.merge(features, df[['상가업소번호','sucess']], how='left', on='상가업소번호')

# 모델 입력 변수 리스트
cols = [
    '층정보',
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
    '매출_임대료_비율',
    '추정_순이익'
]

# 결측 제거 및 상관관계 분석
selected = features_with_label[cols].dropna()
correlation = selected.corr(numeric_only=True)['sucess'].sort_values(ascending=False)
print(correlation)
