# GitHub 저장소와 jsDelivr CDN을 활용한 JSON 파일 호스팅 가이드

GitHub의 공개 저장소와 jsDelivr CDN을 연동하면 JSON 파일을 무료로 호스팅하고 전 세계에 빠르게 배포할 수 있습니다.

이 가이드는 초보자도 쉽게 따라 할 수 있도록 단계별 절차와 함께 제한 사항 및 운영 시 유의사항을 정리했습니다.


# 목차

1. GitHub 저장소 생성
2. JSON 파일 업로드
3. jsDelivr CDN 주소 생성
4. CDN 주소 사용 및 확인
5. 중요 참고사항
6. 참고자료



# 1단계: GitHub 저장소 생성

## 저장소 생성 절차

1. GitHub 로그인
2. 우측 상단 + 버튼 클릭
3. New repository 선택
4. 저장소 이름 입력

예시:

text my-json-data 

5. 저장소 공개 설정

text Public 

> jsDelivr은 공개 저장소만 지원합니다.

6. Add a README file 체크
7. Create repository 클릭



# 2단계: JSON 파일 업로드

생성된 저장소에서:

1. Add file
2. Upload files
3. JSON 파일 업로드
4. Commit changes 클릭

예시 구조:

text my-json-data/ ├── README.md └── data.json 



# 3단계: jsDelivr CDN 주소 생성

## 기본 URL 형식

text https://cdn.jsdelivr.net/gh/사용자명/저장소명/파일경로 

### 예시

| 항목 | 값 |
|--------|--------|
| 사용자명 | honggildong |
| 저장소명 | my-json-data |
| 파일명 | data.json |

생성 URL:

text https://cdn.jsdelivr.net/gh/honggildong/my-json-data/data.json 



## URL 구조 설명

text https://cdn.jsdelivr.net/gh/user/repo@version/file 

| 항목 | 설명 |
|--------|--------|
| user | GitHub 사용자명 또는 조직명 |
| repo | 저장소명 |
| version | 브랜치, 태그, 커밋 해시 |
| file | 파일 경로 |

예시:

text https://cdn.jsdelivr.net/gh/honggildong/my-json-data@v1.0.0/data.json 



# 4단계: CDN 주소 사용 및 확인

## 웹 브라우저 확인

생성된 URL을 브라우저 주소창에 입력합니다.

text https://cdn.jsdelivr.net/gh/honggildong/my-json-data/data.json 

JSON 내용이 표시되면 성공입니다.



## JavaScript에서 사용

html <script> fetch('https://cdn.jsdelivr.net/gh/honggildong/my-json-data/data.json')   .then(response => response.json())   .then(data => console.log(data))   .catch(error => console.error(error)); </script> 



## cURL 테스트

bash curl https://cdn.jsdelivr.net/gh/honggildong/my-json-data/data.json 



# 💡 중요 참고사항

## 1. 캐싱 문제와 버전 관리

jsDelivr는 CDN 캐싱을 적극적으로 사용합니다.

### 일반 캐시 정책

| 방식 | 캐시 기간 |
|--------|--------|
| 브랜치 참조 | 약 12시간 |
| @latest | 최대 7일 |

따라서 파일을 수정해도 즉시 반영되지 않을 수 있습니다.



## 권장 방법: Git 태그 사용

### 릴리스 생성

1. 저장소 이동
2. Releases
3. Draft a new release
4. 버전 입력

예시:

text v1.0.0 v1.0.1 v1.1.0 

5. Publish release



### 버전 고정 URL 사용

text https://cdn.jsdelivr.net/gh/사용자명/저장소명@v1.0.0/data.json 



### 태그 URL 캐시 정책

- 최대 1년 캐시
- S3에 영구 저장

프로덕션 서비스에서는 태그 URL 사용을 권장합니다.



## 2. GitHub 저장소 크기 제한

| 항목 | 제한 |
|--------|--------|
| 권장 저장소 크기 | 1GB 미만 |
| GitHub 경고 | 1GB 초과 |
| 단일 파일 제한 | 100MB |
| 비공식 최대 크기 | 약 5GB |



## GitHub Packages 데이터 전송

Free 플랜 기준:

text 월 1GB 



## 3. jsDelivr 대역폭 제한

### 장점

jsDelivr 자체

- 대역폭 제한 없음
- 무료 사용
- 글로벌 CDN



### 참고

GitHub Pages는 별도 제한 존재

text 월 100GB 



## 4. jsDelivr 사용 제한

| 항목 | 제한 |
|--------|--------|
| 패키지 크기 | 150MB |
| 단일 파일 | 20MB |
| HTML 파일 | text/plain 제공 |



### 지원되지 않는 경우

text Packages larger than 150 MB Single files larger than 20 MB 



## 5. 캐시 퍼지(Purge)

긴급하게 캐시를 갱신해야 하는 경우 사용합니다.

### cURL 예시

bash curl https://purge.jsdelivr.net/gh/사용자명/저장소명@버전/파일경로 

예시:

bash curl https://purge.jsdelivr.net/gh/honggildong/my-json-data@v1.0.0/data.json 



### 웹 인터페이스

jsDelivr 공식 Purge Tool 사용

text https://www.jsdelivr.com/tools/purge 



# 참고자료

| 자료 | 설명 |
|--------|--------|
| jsDelivr 공식 홈페이지 | CDN 서비스 |
| jsDelivr GitHub 저장소 | 소스 코드 |
| jsDelivr Purge Tool | 캐시 제거 |
| GitHub 저장소 제한 문서 | 저장소 용량 정책 |
| GitHub Billing Docs | 데이터 전송 정책 |
| jsDelivr GitHub Delivery Docs | URL 구조 및 캐시 정책 |



# ✅ 운영 체크리스트

- [ ] GitHub 공개 저장소 생성
- [ ] JSON 파일 업로드
- [ ] jsDelivr URL 생성
- [ ] 브라우저 테스트 완료
- [ ] JavaScript fetch 테스트 완료
- [ ] Git Release 태그 생성
- [ ] 버전 URL 적용
- [ ] 캐시 정책 확인
- [ ] 데이터 전송량 모니터링

---

# ⚠️ 주의사항

본 방법은 다음 용도에 적합합니다.

- 개인 프로젝트
- 개발 및 테스트
- 소규모 서비스
- 설정 파일(JSON) 배포
- 정적 데이터 제공

다음 환경에서는 별도 CDN 또는 Object Storage 사용을 권장합니다.

- 대규모 상용 서비스
- 금융 시스템
- 미션 크리티컬 서비스
- 실시간 대용량 데이터 서비스

GitHub 저장소를 단순 파일 저장소로 과도하게 사용하는 경우 GitHub 이용약관에 저촉될 수 있으므로 주의해야 합니다.



## 결론

GitHub + jsDelivr 조합은 무료이면서도 매우 강력한 정적 JSON 배포 방법입니다.

특히:

- API 설정 파일
- LLM 프롬프트 데이터
- 주식/암호화폐 메타데이터
- 버전 관리가 필요한 정적 데이터

배포에 매우 적합하며, Git 태그 기반 버전 관리를 함께 적용하면 안정적인 프로덕션 운영도 가능합니다.
