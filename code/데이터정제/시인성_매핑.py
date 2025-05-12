# 카페 매핑 데이터랑 연결
import pandas as pd
visibility = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\대용량\건물_도로_시인성_분석_0509.csv')
# 고유번호별로 건축물 면적이 가장 큰 행만 남기기
visibility_sorted = visibility.sort_values(by='건축물면적(㎡)', ascending=False)
# 고유번호별로 첫 번째 행만 남기기
visibility_unique = visibility_sorted.drop_duplicates(subset='고유번호', keep='first')
visibility_unique.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\대용량\건물_도로_시인성_분석_0509_중복제거.csv')

area = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\temp_카페_면적_예상.csv')
cafes = pd.read_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\카페_상권_매핑_데이터_중복제거.csv')

# print(area.columns.tolist())
['상가업소번호', '상호명', '지점명', 'TRDAR_CD', '법정동코드', '지번본번지', '지번부번지', '건물관리번호', '지번', '고유번호', '연면적', '건축물면적(㎡)', '커버건축물면적', '커버연면적']
# print(cafes.columns.tolist())
['상가업소번호', '상호명', '지점명', 'TRDAR_CD', 'TRDAR_CD_N', '상권업종소분류코드', '상권업종소분류명', '시도코드', '시도명', '시군구코드', '시군구명', '행정동코드', '행정동명', '법정동코드', '법정동명', '지번코드', '대지구분코드', '대지구분명', '지번본번지', '지번부번지', '지번주소', '도로명코드', '도로명', '건물본번지', '건물부번지', '건물관리번호', '건물명', '도로명주소', '신우편번호', '동정보', '층정보', '호정보', '경도', '위도']
# print(visibility.columns.tolist())
['고유번호', '법정동코드', '지번', '건축물면적(㎡)', '접한길이_m', '도로2m이내접촉길이_m', '교차로_존재_여부']

visibility_copy = pd.merge(area[['상가업소번호','법정동코드','고유번호','지번','상호명', '지점명', 'TRDAR_CD']], visibility_unique, how='left', on=['고유번호','법정동코드','지번'])
print(visibility_copy['상가업소번호'].value_counts())

# 결과 출력
visibility_copy.to_csv(r'C:\Users\iq750\bootcamp_git\Final-Project-2_Team1\data\카페_시인성정보.csv')