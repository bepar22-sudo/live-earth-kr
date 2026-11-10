# 🌏 지구 실시간 보기 (Live Earth)

**대구과학대학교 측지정보과** 교육용 웹 프로그램입니다.
항공기·국제우주정거장·GPS 위성·지진·낮과 밤을 3D 지구 위에서 실시간으로 봅니다.
설치할 것 없이 휴대폰·태블릿·컴퓨터 브라우저에서 바로 열립니다.

### ▶ 바로 보기: **https://bepar22-sudo.github.io/live-earth-kr/**

| 휴대폰 | 컴퓨터 |
|---|---|
| 아래쪽 설명 카드 + 「☰ 자료」 서랍 | 왼쪽 아래 설명 카드 + 오른쪽 자료 패널 |

## 무엇을 볼 수 있나요

열면 **자동 둘러보기**가 시작됩니다(6장면, 한 바퀴 약 3분 30초). 지구를 손가락·마우스로 만지면 멈추고 직접 탐색할 수 있습니다. ▶ 단추를 누르면 다시 둘러봅니다.

| 장면 | 내용 | 알아보기 |
|---|---|---|
| 한반도 하늘의 비행기 | 지금 한반도 주변 항공기 | 항공기 위치 발신(ADS-B) |
| 비행기 따라가기 | 한 대를 따라가며 편명·기종·고도·속도 | 피트·노트 단위 |
| 국제우주정거장 | ISS를 따라가며 고도·속도·위치 | 궤도요소(TLE)와 궤도 계산 |
| **GPS 위성** | GPS 위성과 궤도, 대구 하늘에 지금 보이는 위성 수 | **GNSS 측위 원리 (위성 4개 이상)** |
| 세계 지진 | 최근 24시간 지진 | 판 경계, 규모와 에너지 |
| 낮과 밤 | 실제 태양 위치, 다음 로켓 발사 | 명암 경계선과 표준시 |

직접 탐색할 때: 항공기·위성·지진을 누르면 정보가 나오고 「따라가기」를 할 수 있습니다. 「☰ 자료」에서 위성 종류(우주정거장·GPS·기상·정지궤도·스타링크·전체 등), 지진 기간, 장소 검색, 화면 효과(야간투시·열화상·CRT·흑백)를 고릅니다.

컴퓨터 단축키: `Space` 둘러보기 켜기/멈춤 · `1`~`5` 화면 효과 · `Esc` 따라가기 멈춤
주소 끝에 `?scene=3`(GPS 장면부터), `?tour=0`(둘러보기 없이 시작)을 붙일 수 있습니다.

## 자료는 어떻게 오나요

| 자료 | 출처 | 갱신 |
|---|---|---|
| 위성사진 바탕·지명 | Esri World Imagery | 지도 타일 |
| 항공기 | [adsb.lol](https://adsb.lol) (ODbL) | GitHub Actions가 약 10분마다 받아 둠 (브라우저가 직접 받을 수 없음) |
| 위성 궤도 | [CelesTrak](https://celestrak.org) | 2시간마다 받아 둠 (요청 규칙) |
| 로켓 발사 | [The Space Devs](https://thespacedevs.com) | 약 10분마다 받아 둠 (교실 여러 명이 접속해도 한도에 걸리지 않게) |
| 지진 | [USGS](https://earthquake.usgs.gov) | 브라우저가 1분마다 직접 |
| 야경·구름 사진 | NASA GIBS (Black Marble, MODIS) | 하루 단위 |

3D 지구는 [CesiumJS](https://cesium.com/platform/cesiumjs/), 위성 위치 계산은 [satellite.js](https://github.com/shashwatak/satellite-js)(SGP4)를 씁니다.

> 교육용입니다. 자료는 늦거나 빠질 수 있으니 항법·재난 대응 등 안전 판단에 쓰지 마세요.

## 수업에서 실시간으로 쓰기 (선택)

GitHub 사이트의 항공기는 약 10분 간격입니다. 교실 PC에서 **진짜 실시간**(10초마다, 보고 있는 곳 주변)으로 쓰려면 Python 3만 있으면 됩니다(추가 설치 없음).

```bash
git clone https://github.com/bepar22-sudo/live-earth-kr.git
cd live-earth-kr
python server.py --open
```

브라우저에 `http://127.0.0.1:8780` 이 열립니다. 창을 닫으면 꺼집니다.

## 폴더 구성

```
index.html              화면 (이 파일 하나가 프로그램)
assets/                 흰색 학교 로고, 아이콘, 글꼴(페이퍼로지)
scripts/build_data.py   자료 받기 (GitHub Actions가 실행)
.github/workflows/      10분마다 자료를 받아 사이트에 올리는 설정
server.py               교실 PC용 실시간 중계 서버 (선택)
```

## 라이선스

코드는 MIT. 학교 로고·글꼴·자료는 각자의 조건을 따릅니다([LICENSE](LICENSE)).
원본 아이디어: [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view) (MIT) — 이 저장소는 그 코드를 쓰지 않고 교육용으로 새로 만든 경량판입니다.
