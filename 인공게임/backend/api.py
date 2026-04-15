from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import json

HOST = "127.0.0.1"
PORT = 8000

ADVISORS = [
    {
        "id": "ops-chief",
        "name": "서준",
        "role": "관제 총괄",
        "bio": "서비스 연속성과 운영 안정성 판단을 맡는다.",
        "quote": "같은 차단 조치라도 어디서 끊느냐에 따라 피해가 달라진다.",
    },
    {
        "id": "ir-lead",
        "name": "미아",
        "role": "침해대응 리드",
        "bio": "계정 침해, 악성코드 확산, 초기 흔적 추적을 담당한다.",
        "quote": "오판은 무지해서가 아니라, 그럴듯한 선택을 서둘러 믿을 때 나온다.",
    },
    {
        "id": "legal-ciso",
        "name": "도경",
        "role": "대외 대응 자문",
        "bio": "고객 공지, 신고 의무, 평판 리스크를 관리한다.",
        "quote": "기술 조치가 맞아도 설명이 틀리면 사고는 끝나지 않는다.",
    },
    {
        "id": "ot-analyst",
        "name": "하민",
        "role": "산업제어 분석가",
        "bio": "설비망과 업무망이 얽힌 사건을 본다.",
        "quote": "운영을 계속하는 선택도 때론 가장 위험한 도박이 된다.",
    },
]

CHECKLIST = [
    {
        "id": "identity-lockdown",
        "label": "계정 잠금, 세션 만료, MFA 재등록",
        "kind": "계정 통제",
        "summary": "계정 탈취, 원격 접속 남용, BEC 정황에서 권한을 빨리 끊는 조치.",
    },
    {
        "id": "segment-isolation",
        "label": "감염 구간 격리와 확산 차단",
        "kind": "확산 통제",
        "summary": "랜섬웨어나 악성코드가 내부망에서 퍼질 때 범위를 줄이는 선택.",
    },
    {
        "id": "traffic-mitigation",
        "label": "트래픽 우회, 필터링, 레이트 리밋",
        "kind": "서비스 방어",
        "summary": "대량 요청과 과부하 상황에서 정상 사용자의 경로를 살리는 대응.",
    },
    {
        "id": "egress-freeze",
        "label": "외부 전송 차단과 데이터 반출 통제",
        "kind": "반출 통제",
        "summary": "정보 유출이 의심될 때 외부 업로드와 반출 경로를 묶는 조치.",
    },
    {
        "id": "vendor-freeze",
        "label": "공급망 업데이트 중단과 배포 동결",
        "kind": "배포 통제",
        "summary": "업데이트 직후 이상이 생길 때 더 퍼지지 않게 배포를 멈추는 판단.",
    },
    {
        "id": "patch-emergency",
        "label": "긴급 패치와 취약 서비스 임시 차단",
        "kind": "취약점 대응",
        "summary": "공개 직후 악용되는 취약점에 즉시 손대는 대응.",
    },
    {
        "id": "dns-sinkhole",
        "label": "악성 도메인 차단과 DNS 싱크홀",
        "kind": "연결 차단",
        "summary": "봇넷 제어 통신과 악성 인프라 연결을 줄이는 조치.",
    },
    {
        "id": "failover-cutover",
        "label": "예비 시스템 전환",
        "kind": "운영 전환",
        "summary": "핵심 서비스만 유지하며 전체 중단을 피하는 선택.",
    },
    {
        "id": "ot-manual-mode",
        "label": "설비망 수동 운전 전환",
        "kind": "안전 우선",
        "summary": "산업제어 환경에서 자동 제어보다 안전을 우선하는 대응.",
    },
    {
        "id": "mail-filter-tighten",
        "label": "메일 필터 강화와 유사 도메인 차단",
        "kind": "유입 차단",
        "summary": "사람을 노리는 메일 기반 공격의 재유입을 줄이는 조치.",
    },
    {
        "id": "backup-audit",
        "label": "백업 무결성 점검",
        "kind": "복구 확인",
        "summary": "최악의 상황이 와도 돌아갈 수 있는지 먼저 확인하는 선택.",
    },
    {
        "id": "staff-briefing",
        "label": "직원 경보 발령과 추가 클릭 차단 안내",
        "kind": "내부 공지",
        "summary": "사람을 노리는 사고에서 추가 클릭과 재확산을 줄인다.",
    },
    {
        "id": "forensics-priority",
        "label": "포렌식 우선 수집과 증적 보존",
        "kind": "원인 분석",
        "summary": "원인과 이동 경로를 파악하고 재발 방지 근거를 남긴다.",
    },
    {
        "id": "public-briefing",
        "label": "고객 공지 초안과 대외 메시지 준비",
        "kind": "대외 대응",
        "summary": "민원과 신뢰 하락을 줄이기 위한 설명 준비.",
    },
    {
        "id": "customer-support-surge",
        "label": "고객센터 인력 증원",
        "kind": "운영 지원",
        "summary": "로그인 장애, 결제 문제, 데이터 유출 의심 상황의 문의 폭주를 완화한다.",
    },
    {
        "id": "network-hunt",
        "label": "내부 트래픽 수색과 흔적 추적",
        "kind": "확산 탐색",
        "summary": "이미 번졌는지, 어디까지 갔는지 찾는 사후 확인 조치.",
    },
    {
        "id": "legal-review",
        "label": "법무 검토와 보고 의무 확인",
        "kind": "규제 대응",
        "summary": "개인정보나 결제정보, 의료정보가 걸린 사고에서 필요한 절차를 정리한다.",
    },
    {
        "id": "partner-notice",
        "label": "협력사 통지와 연동 시스템 점검 요청",
        "kind": "연동 대응",
        "summary": "공급망, API 연동, 물류·결제 파트너까지 범위를 넓혀 확인한다.",
    },
    {
        "id": "global-restart",
        "label": "원인 분석 없이 전체 재시작",
        "kind": "즉흥 복구",
        "summary": "빨리 정상화하고 싶을 때 떠오르지만 증적과 범위 파악을 놓칠 수 있다.",
    },
    {
        "id": "full-blackout",
        "label": "외부 접속 전면 차단",
        "kind": "강경 차단",
        "summary": "강해 보이지만 서비스 피해까지 함께 키울 수 있는 선택.",
    },
    {
        "id": "wait-more-logs",
        "label": "로그가 더 쌓일 때까지 관찰 유지",
        "kind": "판단 보류",
        "summary": "신중해 보이지만 확산형 사고에서는 시간을 그대로 넘겨줄 수 있다.",
    },
    {
        "id": "trust-signature",
        "label": "정상 서명만 믿고 그대로 배포 유지",
        "kind": "관성 유지",
        "summary": "공급망 사고에서 흔히 나오는 방심 패턴.",
    },
    {
        "id": "disable-monitoring",
        "label": "탐지 경보를 꺼서 소음 줄이기",
        "kind": "관측 축소",
        "summary": "혼란을 줄이는 것처럼 보이지만 이후 상황을 더 보지 못하게 된다.",
    },
    {
        "id": "keep-production",
        "label": "설비와 서비스 계속 가동",
        "kind": "운영 우선",
        "summary": "당장 멈추지 않겠다는 선택이 더 큰 물리 피해로 이어질 수 있다.",
    },
]

INCIDENTS = [
    {
        "id": "phishing-credential",
        "name": "인사팀 사칭 피싱 메일 확산",
        "threatLevel": "중간",
        "brief": "급여 명세 확인 링크를 가장한 메일이 여러 부서에 동시 확산되고 있다.",
        "target": "직원 계정, 메일 시스템, 사내 포털",
        "symptoms": ["로그인 실패 급증", "유사 도메인 클릭 제보 증가", "새벽 해외 IP 로그인 흔적"],
        "consequences": ["계정 탈취", "추가 피싱 발송", "내부 시스템 접근 확대"],
        "advisorId": "ir-lead",
        "requiredActions": ["identity-lockdown", "mail-filter-tighten"],
        "helpfulActions": ["staff-briefing", "network-hunt"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 26,
        "impact": {"trust": -8, "ops": -4},
        "report": {
            "success": "계정과 메일 유입 경로를 함께 막아 추가 클릭과 재로그인을 빠르게 줄였다.",
            "partial": "계정 또는 메일 중 한쪽만 손봐서 확산 속도는 줄었지만 재시도가 남았다.",
            "failure": "관찰을 유지하는 동안 추가 클릭과 로그인 재시도가 이어져 피해 범위가 넓어졌다.",
        },
    },
    {
        "id": "ransomware-files",
        "name": "공유 파일 서버 랜섬웨어 징후",
        "threatLevel": "높음",
        "brief": "공유 문서가 열리지 않고 파일명 패턴이 비정상적으로 바뀌고 있다.",
        "target": "파일 서버, 직원 PC, 백업 체계",
        "symptoms": ["파일 확장자 일괄 변경", "백업 작업 실패 증가", "디스크 사용량 급증"],
        "consequences": ["문서 접근 불가", "복구 지연", "업무 중단"],
        "advisorId": "ops-chief",
        "requiredActions": ["segment-isolation"],
        "helpfulActions": ["backup-audit", "forensics-priority"],
        "harmfulActions": ["global-restart", "disable-monitoring"],
        "reward": 38,
        "impact": {"trust": -6, "ops": -18},
        "report": {
            "success": "감염 구간을 빨리 잘라내고 복구 가능성까지 확인해 장기 중단을 줄였다.",
            "partial": "격리는 했지만 복구선 확인이 늦어 운영 차질이 예상보다 길어졌다.",
            "failure": "재시작이나 탐지 축소는 암호화 범위와 흔적을 더 흐리게 만들어 복구를 어렵게 했다.",
        },
    },
    {
        "id": "ddos-portal",
        "name": "고객 포털 대량 요청 공격",
        "threatLevel": "중간",
        "brief": "로그인과 결제 진입 페이지에 대량 요청이 몰려 정상 고객이 접속하지 못한다.",
        "target": "웹 포털, 네트워크 경계, 고객 경험",
        "symptoms": ["응답 지연 급증", "동일 패턴 요청 반복", "일부 지역 접속 불가"],
        "consequences": ["서비스 중단", "이탈 고객 증가", "브랜드 신뢰 하락"],
        "advisorId": "ops-chief",
        "requiredActions": ["traffic-mitigation"],
        "helpfulActions": ["failover-cutover", "customer-support-surge"],
        "harmfulActions": ["full-blackout", "wait-more-logs"],
        "reward": 28,
        "impact": {"trust": -14, "ops": -10},
        "report": {
            "success": "요청을 거르면서 정상 사용자의 경로를 살려 서비스 중단을 짧게 묶었다.",
            "partial": "트래픽 방어는 했지만 안내와 우회 운영이 약해 고객 불편이 오래 남았다.",
            "failure": "전면 차단은 공격보다 서비스 피해를 더 크게 보이게 만들었다.",
        },
    },
    {
        "id": "db-exfiltration",
        "name": "고객 정보 반출 의심",
        "threatLevel": "매우 높음",
        "brief": "야간 시간대에 고객 데이터 조회량과 외부 전송량이 동시에 급증했다.",
        "target": "고객 DB, 외부 전송 구간, 개인정보",
        "symptoms": ["비정상 대량 조회", "권한 상승 흔적", "외부 업로드 급증"],
        "consequences": ["개인정보 유출", "법적 대응 비용 증가", "장기 신뢰 손상"],
        "advisorId": "legal-ciso",
        "requiredActions": ["egress-freeze"],
        "helpfulActions": ["forensics-priority", "legal-review", "public-briefing"],
        "harmfulActions": ["wait-more-logs", "disable-monitoring"],
        "reward": 46,
        "impact": {"trust": -24, "ops": -6},
        "report": {
            "success": "반출을 먼저 묶고 증적과 신고 절차를 정리해 유출 규모와 후폭풍을 줄였다.",
            "partial": "반출 차단은 했지만 규제 대응과 증적 정리가 늦어 사후 비용이 커졌다.",
            "failure": "조금 더 보자는 판단이 실제 반출 시간만 늘려 피해를 키웠다.",
        },
    },
    {
        "id": "supply-chain-alert",
        "name": "업데이트 직후 공급망 이상 징후",
        "threatLevel": "높음",
        "brief": "새 버전 배포 이후 여러 고객사 PC에서 동일한 비정상 프로세스가 동시에 발견된다.",
        "target": "업데이트 체계, 배포 서버, 신뢰 체인",
        "symptoms": ["배포 직후 CPU 급증", "동일 해시 프로세스 반복", "배포 시점과 이상 시점 일치"],
        "consequences": ["다수 고객 확산", "배포 신뢰 붕괴", "협력사 피해 동반"],
        "advisorId": "ir-lead",
        "requiredActions": ["vendor-freeze"],
        "helpfulActions": ["partner-notice", "forensics-priority"],
        "harmfulActions": ["trust-signature"],
        "reward": 40,
        "impact": {"trust": -16, "ops": -10},
        "report": {
            "success": "배포를 멈추고 파트너 범위까지 점검해 공급망 전체 확산을 줄였다.",
            "partial": "배포는 멈췄지만 외부 연동과 원인 추적이 늦어 여진이 남았다.",
            "failure": "정상 서명만 믿고 유지한 선택은 공급망 사고의 전형적인 오판이었다.",
        },
    },
    {
        "id": "botnet-c2",
        "name": "봇넷 제어 통신 정황",
        "threatLevel": "높음",
        "brief": "여러 업무용 PC가 같은 외부 도메인으로 규칙적으로 연결을 시도하고 있다.",
        "target": "엔드포인트, DNS, 외부 제어 통신",
        "symptoms": ["반복 도메인 질의", "업무 시간 외 동일 주기 통신", "탐지는 약하지만 트래픽은 지속"],
        "consequences": ["추가 명령 수신", "내부 이동 확대", "데이터 탈취 준비"],
        "advisorId": "ir-lead",
        "requiredActions": ["dns-sinkhole"],
        "helpfulActions": ["network-hunt", "forensics-priority"],
        "harmfulActions": ["disable-monitoring", "wait-more-logs"],
        "reward": 34,
        "impact": {"trust": -8, "ops": -9},
        "report": {
            "success": "제어 통신을 끊고 추가 감염 자산을 추적해 재명령 수신을 막았다.",
            "partial": "도메인 차단은 했지만 내부 수색이 부족해 잔존 감염 우려가 남았다.",
            "failure": "소음을 줄이려 관측을 꺼버리면 실제 남은 감염 범위를 더 보지 못한다.",
        },
    },
    {
        "id": "zero-day-web",
        "name": "공개된 웹 취약점 악용 시도",
        "threatLevel": "매우 높음",
        "brief": "새로 공개된 취약점과 유사한 요청 패턴이 고객 포털에 집중되고 있다.",
        "target": "웹 애플리케이션, 관리자 페이지, 고객 데이터",
        "symptoms": ["특정 URL 요청 폭증", "에러 로그 패턴 반복", "관리 콘솔 접근 시도 증가"],
        "consequences": ["서버 장악 가능성", "데이터 접근 확대", "웹 변조 위험"],
        "advisorId": "ops-chief",
        "requiredActions": ["patch-emergency"],
        "helpfulActions": ["failover-cutover", "forensics-priority"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 48,
        "impact": {"trust": -11, "ops": -11},
        "report": {
            "success": "취약 경로를 바로 닫고 우회 운영까지 준비해 공격 창구를 빠르게 줄였다.",
            "partial": "패치는 했지만 서비스 전환과 분석이 약해 운영 충격이 오래 남았다.",
            "failure": "조금 더 보자는 판단이 취약점 악용 시간만 더 벌어준 셈이 됐다.",
        },
    },
    {
        "id": "ot-network-breach",
        "name": "생산 설비망 침입 의심",
        "threatLevel": "매우 높음",
        "brief": "설비 모니터링 화면에 없는 명령 이력이 남고 제어망 지연이 발생한다.",
        "target": "설비망, 제어 시스템, 안전 운영",
        "symptoms": ["제어 명령 이력 불일치", "설비 응답 지연", "업무망과 설비망 간 로그 급증"],
        "consequences": ["생산 중단", "설비 손상", "안전사고 가능성"],
        "advisorId": "ot-analyst",
        "requiredActions": ["ot-manual-mode"],
        "helpfulActions": ["network-hunt", "legal-review"],
        "harmfulActions": ["keep-production"],
        "reward": 52,
        "impact": {"trust": -12, "ops": -20},
        "report": {
            "success": "수동 전환으로 안전을 확보하고 흔적을 추적해 물리 피해 가능성을 낮췄다.",
            "partial": "전환은 했지만 원인 추적이 약해 재가동 판단이 불안정하게 남았다.",
            "failure": "설비를 계속 돌리는 선택은 짧은 생산 유지와 긴 물리 피해를 맞바꾸는 경우가 많다.",
        },
    },
    {
        "id": "bec-wirefraud",
        "name": "임원 사칭 송금 요청",
        "threatLevel": "높음",
        "brief": "재무팀이 임원 메일을 사칭한 긴급 송금 요청을 실제 결재 직전까지 진행했다.",
        "target": "재무팀, 메일, 승인 프로세스",
        "symptoms": ["급한 송금 요구", "외부 메신저 재촉", "전화 재확인 회피"],
        "consequences": ["금전 손실", "내부 통제 실패", "대외 신뢰 하락"],
        "advisorId": "legal-ciso",
        "requiredActions": ["identity-lockdown", "mail-filter-tighten"],
        "helpfulActions": ["staff-briefing", "legal-review"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 33,
        "impact": {"trust": -11, "ops": -5},
        "report": {
            "success": "사칭 채널과 계정 유입을 동시에 차단해 추가 송금 시도를 막았다.",
            "partial": "송금은 막았지만 재발 방지 안내가 약해 비슷한 시도가 다시 먹힐 여지가 남았다.",
            "failure": "신중하게 더 보자는 선택이 오히려 결재 승인 시간을 열어두는 결과가 됐다.",
        },
    },
    {
        "id": "credential-stuffing",
        "name": "대량 로그인 시도와 계정 탈취",
        "threatLevel": "중간",
        "brief": "고객 계정에 짧은 시간 동안 비정상적인 로그인 시도가 몰리고 있다.",
        "target": "고객 계정, 로그인 API, 고객센터",
        "symptoms": ["실패 로그인 급증", "잠금 계정 증가", "다수 국가에서 동시 시도"],
        "consequences": ["계정 탈취", "고객 문의 급증", "서비스 이탈"],
        "advisorId": "ir-lead",
        "requiredActions": ["identity-lockdown"],
        "helpfulActions": ["customer-support-surge", "public-briefing"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 27,
        "impact": {"trust": -13, "ops": -5},
        "report": {
            "success": "계정 통제를 먼저 걸고 고객 안내를 보완해 탈취와 민원을 함께 줄였다.",
            "partial": "계정 보호는 했지만 고객 안내가 약해 불만과 혼선이 오래 남았다.",
            "failure": "로그를 더 보며 기다리면 이미 시도 중인 계정 탈취를 그대로 흘려보내게 된다.",
        },
    },
    {
        "id": "cloud-misconfig",
        "name": "클라우드 저장소 공개 노출",
        "threatLevel": "높음",
        "brief": "검색 엔진에서 내부 문서 저장소의 공개 URL이 노출된 정황이 확인됐다.",
        "target": "클라우드 저장소, 문서, 권한 설정",
        "symptoms": ["공개 링크 인덱싱", "비인가 다운로드 기록", "민감 문서 접근 흔적"],
        "consequences": ["문서 유출", "브랜드 신뢰 손상", "규제 리스크"],
        "advisorId": "legal-ciso",
        "requiredActions": ["egress-freeze"],
        "helpfulActions": ["legal-review", "public-briefing", "forensics-priority"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 37,
        "impact": {"trust": -15, "ops": -4},
        "report": {
            "success": "외부 노출을 먼저 닫고 사후 절차를 정리해 확산과 설명 리스크를 줄였다.",
            "partial": "노출은 막았지만 이미 누가 받았는지 추적이 약해 후속 대응이 무거워졌다.",
            "failure": "지켜보는 동안 공개 링크는 계속 남아 있었고 다운로드 가능 시간만 늘어났다.",
        },
    },
    {
        "id": "pos-malware",
        "name": "결제 단말 악성코드 의심",
        "threatLevel": "높음",
        "brief": "매장 결제 단말에서 설명되지 않는 프로세스와 외부 통신이 관찰된다.",
        "target": "결제 단말, 매장망, 카드정보 처리 구간",
        "symptoms": ["단말 지연 증가", "미확인 외부 통신", "매장 결제 오류 증가"],
        "consequences": ["결제정보 유출", "오프라인 영업 차질", "민원 증가"],
        "advisorId": "ops-chief",
        "requiredActions": ["segment-isolation"],
        "helpfulActions": ["network-hunt", "forensics-priority", "public-briefing"],
        "harmfulActions": ["global-restart"],
        "reward": 36,
        "impact": {"trust": -14, "ops": -12},
        "report": {
            "success": "단말 구간을 잘라 카드정보 처리 경로를 분리하고 피해 확산을 줄였다.",
            "partial": "격리는 했지만 고객 공지와 흔적 확보가 늦어 사후 정산 부담이 남았다.",
            "failure": "전체 재시작은 빨라 보이지만 감염 범위와 카드정보 노출 경로를 흐리게 만든다.",
        },
    },
    {
        "id": "remote-access-abuse",
        "name": "관리자 원격 접속 채널 악용",
        "threatLevel": "높음",
        "brief": "관리자 원격 접속 계정으로 심야 시간대 연속 로그인 흔적이 남고 있다.",
        "target": "관리자 계정, 원격 접속 게이트웨이",
        "symptoms": ["새벽 접속", "권한 상승 시도", "로그 삭제 흔적"],
        "consequences": ["관리 권한 탈취", "내부 이동", "복수 시스템 접근"],
        "advisorId": "ir-lead",
        "requiredActions": ["identity-lockdown"],
        "helpfulActions": ["network-hunt", "forensics-priority"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 35,
        "impact": {"trust": -9, "ops": -12},
        "report": {
            "success": "관리 계정을 끊고 이동 흔적까지 추적해 추가 권한 확장을 막았다.",
            "partial": "접속은 차단했지만 이동 경로를 다 못 찾아 잔존 리스크가 남았다.",
            "failure": "로그를 더 보자는 선택은 이미 열려 있는 관리자 세션 시간을 더 준 셈이다.",
        },
    },
    {
        "id": "wiper-backup-threat",
        "name": "백업 파괴 전조",
        "threatLevel": "매우 높음",
        "brief": "백업 작업이 연속 실패하고 백업 관리자 계정 변경 시도가 포착됐다.",
        "target": "백업 체계, 관리자 계정, 복구 경로",
        "symptoms": ["백업 실패 연속 발생", "관리 계정 권한 변경", "스토리지 삭제 요청 흔적"],
        "consequences": ["복구 불가", "장기 운영 중단", "복구 비용 폭증"],
        "advisorId": "ops-chief",
        "requiredActions": ["segment-isolation", "identity-lockdown"],
        "helpfulActions": ["backup-audit", "forensics-priority"],
        "harmfulActions": ["wait-more-logs", "global-restart"],
        "reward": 50,
        "impact": {"trust": -8, "ops": -21},
        "report": {
            "success": "확산 구간과 관리자 권한을 함께 묶고 복구선을 확인해 최악의 시나리오를 줄였다.",
            "partial": "한 축만 먼저 막아 백업 파괴 자체는 늦췄지만 복구 신뢰가 불안하게 남았다.",
            "failure": "관찰이나 재시작은 백업 공격자가 원하는 시간을 그대로 벌어주는 패턴이다.",
        },
    },
    {
        "id": "hospital-booking-outage",
        "name": "병원 예약 시스템 장애와 데이터 노출 우려",
        "threatLevel": "높음",
        "brief": "예약 포털 장애와 함께 일부 진료 내역 페이지 접근 오류가 보고된다.",
        "target": "예약 시스템, 의료정보, 고객 지원",
        "symptoms": ["예약 실패 증가", "진료 내역 일부 오류", "고객센터 문의 폭주"],
        "consequences": ["진료 일정 차질", "민감 정보 노출 우려", "기관 신뢰 하락"],
        "advisorId": "legal-ciso",
        "requiredActions": ["failover-cutover"],
        "helpfulActions": ["customer-support-surge", "legal-review", "public-briefing"],
        "harmfulActions": ["full-blackout"],
        "reward": 39,
        "impact": {"trust": -16, "ops": -10},
        "report": {
            "success": "예비 경로 전환과 대외 안내를 붙여 진료 차질과 불안을 함께 줄였다.",
            "partial": "서비스는 살렸지만 민감정보 대응 메시지가 약해 신뢰 회복이 더뎠다.",
            "failure": "전면 차단은 민감한 기관 서비스에서 공격보다 더 큰 업무 공백을 만든다.",
        },
    },
    {
        "id": "api-partner-breach",
        "name": "협력사 API 연동 사고 확산",
        "threatLevel": "높음",
        "brief": "연동 파트너 쪽 키 유출 의심 이후 비정상 API 호출량이 늘었다.",
        "target": "외부 연동 API, 파트너 인증 키, 주문 흐름",
        "symptoms": ["비정상 호출량 급증", "낯선 키 사용", "주문 상태 꼬임"],
        "consequences": ["주문 처리 혼선", "연동 장애", "협력사 신뢰 손상"],
        "advisorId": "legal-ciso",
        "requiredActions": ["identity-lockdown", "egress-freeze"],
        "helpfulActions": ["partner-notice", "forensics-priority"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 41,
        "impact": {"trust": -13, "ops": -9},
        "report": {
            "success": "연동 키와 반출 경로를 함께 묶고 파트너 범위까지 확인해 연쇄 장애를 줄였다.",
            "partial": "인증 또는 반출 중 한 축만 제어해 주문 혼선이 예상보다 오래 지속됐다.",
            "failure": "연동 사고는 내부만 보면 늦는다. 관찰 유지로는 파트너 범위 확산을 못 막는다.",
        },
    },
    {
        "id": "account-recovery-fraud",
        "name": "계정 복구 프로세스 악용",
        "threatLevel": "중간",
        "brief": "고객센터를 통한 계정 복구 요청이 급증했고 일부는 본인확인 정보가 어색하다.",
        "target": "고객 계정, 고객센터, 복구 프로세스",
        "symptoms": ["복구 요청 급증", "유사한 스크립트형 통화", "복구 직후 결제 시도"],
        "consequences": ["계정 탈취", "상담 품질 저하", "고객 불신"],
        "advisorId": "ir-lead",
        "requiredActions": ["identity-lockdown"],
        "helpfulActions": ["customer-support-surge", "staff-briefing"],
        "harmfulActions": ["wait-more-logs"],
        "reward": 29,
        "impact": {"trust": -10, "ops": -6},
        "report": {
            "success": "복구 절차를 즉시 강화해 사회공학 기반 탈취를 빠르게 끊어냈다.",
            "partial": "계정 통제는 했지만 상담 조직 안내가 약해 현장 혼선이 남았다.",
            "failure": "상담 품질을 믿고 더 보자는 선택은 복구 채널 악용을 계속 열어두는 결과가 됐다.",
        },
    },
]

SCENARIO = {
    "title": "인공게임",
    "subtitle": "의뢰형 보안 사고 대응 시뮬레이션",
    "campaignTitle": "시즌 1 계약 대응 리그",
    "company": "Freelance SOC Unit",
    "goal": "회사별 의뢰를 고르고 고정 체크리스트로 대응안을 제출해 코인을 모아라.",
    "maxSelections": 3,
    "advisors": ADVISORS,
    "checklist": CHECKLIST,
    "incidents": INCIDENTS,
}


def send_json(handler, payload, status=200):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            send_json(self, {"ok": True})
            return
        if path == "/api/game-data":
            send_json(self, SCENARIO)
            return
        send_json(self, {"error": "not_found"}, 404)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Python API running on http://{HOST}:{PORT}")
    server.serve_forever()
