const API_BASE = "http://127.0.0.1:8000/api";
const USERS_KEY = "ingong_users";
const SESSION_KEY = "ingong_session_user";
const LEADERBOARD_KEY = "ingong_leaderboard";
const CONTRACT_TARGET = 16;
const MAX_PROCESS_MS = 5000;
const MIN_PROCESS_MS = 1800;

const CLIENTS = [
  "가람회사",
  "나래회사",
  "다온회사",
  "라움회사",
  "마루회사",
  "보람회사",
  "새롬회사",
  "아람회사",
  "이음회사",
  "자람회사",
  "차오름회사",
  "하람회사",
  "aa회사",
  "bb회사",
  "cc회사",
  "dd회사"
];

const state = {
  currentUser: localStorage.getItem(SESSION_KEY) || "",
  contracts: [],
  checklist: [],
  advisors: [],
  goal: "",
  maxSelections: 3,
  selectedContractId: "",
  selectedActionIds: new Set(),
  processing: false,
  processingTimer: null,
  processingStartedAt: 0,
  processingDurationMs: MIN_PROCESS_MS,
  completedContracts: 0,
  coins: 0,
  trust: 81,
  ops: 83,
  timeline: [],
  gameOver: false
};

const refs = {
  authScreen: document.querySelector("#authScreen"),
  gameShell: document.querySelector("#gameShell"),
  authMessage: document.querySelector("#authMessage"),
  signupForm: document.querySelector("#signupForm"),
  loginForm: document.querySelector("#loginForm"),
  showLoginTab: document.querySelector("#showLoginTab"),
  showSignupTab: document.querySelector("#showSignupTab"),
  helpButton: document.querySelector("#helpButton"),
  helpModal: document.querySelector("#helpModal"),
  closeHelpButton: document.querySelector("#closeHelpButton"),
  logoutButton: document.querySelector("#logoutButton"),
  refreshContractsButton: document.querySelector("#refreshContractsButton"),
  playerName: document.querySelector("#playerName"),
  scenarioMeta: document.querySelector("#scenarioMeta"),
  campaignTitle: document.querySelector("#campaignTitle"),
  companyName: document.querySelector("#companyName"),
  campaignGoal: document.querySelector("#campaignGoal"),
  threatBadge: document.querySelector("#threatBadge"),
  incidentName: document.querySelector("#incidentName"),
  incidentBrief: document.querySelector("#incidentBrief"),
  incidentTarget: document.querySelector("#incidentTarget"),
  clientName: document.querySelector("#clientName"),
  contractReward: document.querySelector("#contractReward"),
  symptomList: document.querySelector("#symptomList"),
  consequenceList: document.querySelector("#consequenceList"),
  goalText: document.querySelector("#goalText"),
  turnValue: document.querySelector("#turnValue"),
  turnTotal: document.querySelector("#turnTotal"),
  completedCount: document.querySelector("#completedCount"),
  totalCount: document.querySelector("#totalCount"),
  budgetValue: document.querySelector("#budgetValue"),
  trustValue: document.querySelector("#trustValue"),
  opsValue: document.querySelector("#opsValue"),
  budgetHint: document.querySelector("#budgetHint"),
  checklistGrid: document.querySelector("#checklistGrid"),
  resolveButton: document.querySelector("#resolveButton"),
  resolutionBox: document.querySelector("#resolutionBox"),
  processingStatus: document.querySelector("#processingStatus"),
  progressBar: document.querySelector("#progressBar"),
  contractBoard: document.querySelector("#contractBoard"),
  advisorList: document.querySelector("#advisorList"),
  timeline: document.querySelector("#timeline"),
  summaryPanel: document.querySelector("#summaryPanel"),
  summaryTitle: document.querySelector("#summaryTitle"),
  summaryBody: document.querySelector("#summaryBody"),
  rankIntro: document.querySelector("#rankIntro"),
  rankForm: document.querySelector("#rankForm"),
  rankNameInput: document.querySelector("#rankNameInput"),
  rankMessage: document.querySelector("#rankMessage"),
  leaderboardList: document.querySelector("#leaderboardList"),
  advisorTemplate: document.querySelector("#advisorTemplate"),
  contractTemplate: document.querySelector("#contractTemplate"),
  checklistTemplate: document.querySelector("#checklistTemplate")
};

function clamp(value) {
  return Math.max(0, Math.min(100, value));
}

function shuffle(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swapIndex]] = [copy[swapIndex], copy[index]];
  }
  return copy;
}

function readUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function readLeaderboard() {
  try {
    return JSON.parse(localStorage.getItem(LEADERBOARD_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeLeaderboard(entries) {
  localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(entries));
}

function createContracts(incidents) {
  const shuffledIncidents = shuffle(incidents);
  const clients = shuffle(CLIENTS);
  const contracts = [];

  for (let index = 0; index < CONTRACT_TARGET; index += 1) {
    const incident = shuffledIncidents[index % shuffledIncidents.length];
    contracts.push({
      ...incident,
      id: `${incident.id}-${index}`,
      client: clients[index % clients.length],
      completed: false
    });
  }

  return contracts;
}

async function api(path) {
  const response = await fetch(`${API_BASE}${path}`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || data.error || "request_failed");
  return data;
}

function setAuthMessage(message) {
  refs.authMessage.textContent = message;
}

function showAuth() {
  refs.authScreen.classList.remove("hidden");
  refs.gameShell.classList.add("hidden");
}

function showGame() {
  refs.authScreen.classList.add("hidden");
  refs.gameShell.classList.remove("hidden");
}

function switchAuthTab(mode) {
  const loginMode = mode === "login";
  refs.loginForm.classList.toggle("hidden", !loginMode);
  refs.signupForm.classList.toggle("hidden", loginMode);
  refs.showLoginTab.classList.toggle("active", loginMode);
  refs.showSignupTab.classList.toggle("active", !loginMode);
  setAuthMessage("");
}

function openHelp() {
  refs.helpModal.classList.remove("hidden");
}

function closeHelp() {
  refs.helpModal.classList.add("hidden");
}

function availableContracts() {
  return state.contracts.filter((contract) => !contract.completed);
}

function selectedContract() {
  return state.contracts.find((contract) => contract.id === state.selectedContractId) || null;
}

function updateStats() {
  refs.budgetValue.textContent = state.coins;
  refs.trustValue.textContent = state.trust;
  refs.opsValue.textContent = state.ops;
  refs.turnValue.textContent = state.completedContracts;
  refs.turnTotal.textContent = CONTRACT_TARGET;
  refs.completedCount.textContent = state.completedContracts;
  refs.totalCount.textContent = CONTRACT_TARGET;
}

function renderAdvisors(activeId = "") {
  refs.advisorList.innerHTML = "";
  state.advisors.forEach((advisor) => {
    const fragment = refs.advisorTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".advisor-card");
    fragment.querySelector(".advisor-name").textContent = advisor.name;
    fragment.querySelector(".advisor-role").textContent = advisor.role;
    fragment.querySelector(".advisor-bio").textContent = advisor.bio;
    fragment.querySelector(".advisor-quote").textContent = advisor.quote;
    if (advisor.id === activeId) card.classList.add("active");
    refs.advisorList.appendChild(fragment);
  });
}

function renderTimeline() {
  refs.timeline.innerHTML = "";
  if (state.timeline.length === 0) {
    refs.timeline.innerHTML = '<div class="timeline-item"><strong>처리 기록 없음</strong><p>아직 완료한 회사 의뢰가 없다.</p></div>';
    return;
  }

  state.timeline.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "timeline-item";
    item.innerHTML = `<strong>${entry.client}</strong><p>${entry.text}</p>`;
    refs.timeline.appendChild(item);
  });
}

function renderLeaderboard() {
  const entries = readLeaderboard()
    .sort((left, right) => right.coins - left.coins || left.createdAt.localeCompare(right.createdAt))
    .slice(0, 10);

  refs.leaderboardList.innerHTML = "";
  if (entries.length === 0) {
    refs.leaderboardList.innerHTML = '<div class="timeline-item"><strong>랭킹 없음</strong><p>16개 의뢰를 완료하면 첫 기록을 등록할 수 있다.</p></div>';
    return;
  }

  entries.forEach((entry, index) => {
    const row = document.createElement("div");
    row.className = "rank-row";
    row.innerHTML = `
      <span class="rank-place">${index + 1}</span>
      <div class="rank-copy">
        <strong>${entry.name}</strong>
        <span>${entry.coins} 코인</span>
      </div>
    `;
    refs.leaderboardList.appendChild(row);
  });
}

function renderRankPanel() {
  const canRegister = state.completedContracts >= CONTRACT_TARGET;
  refs.rankIntro.textContent = canRegister
    ? `16개 의뢰를 모두 완료했다. 현재 ${state.coins} 코인으로 랭크를 등록할 수 있다.`
    : `16개 의뢰를 모두 완료하면 코인 개수로 랭크를 등록할 수 있다. 현재 ${state.completedContracts}/16 완료.`;
  refs.rankForm.classList.toggle("hidden", !canRegister);
  refs.rankNameInput.value = canRegister ? state.currentUser : "";
  renderLeaderboard();
}

function renderContractBoard() {
  refs.contractBoard.innerHTML = "";
  const contracts = availableContracts();

  if (contracts.length === 0) {
    refs.contractBoard.innerHTML = '<div class="timeline-item"><strong>모든 의뢰 완료</strong><p>랭크를 등록하거나 새 의뢰 세트를 눌러 다시 시작하면 된다.</p></div>';
    return;
  }

  contracts.forEach((contract) => {
    const fragment = refs.contractTemplate.content.cloneNode(true);
    const button = fragment.querySelector(".contract-card");
    fragment.querySelector(".contract-client").textContent = contract.client;
    fragment.querySelector(".contract-title").textContent = `${contract.client} 의뢰`;
    fragment.querySelector(".contract-threat").textContent = contract.name;
    fragment.querySelector(".contract-reward").textContent = `${contract.reward} 코인`;

    if (state.selectedContractId === contract.id) {
      button.classList.add("selected");
    }

    button.addEventListener("click", () => {
      if (state.processing) return;
      state.selectedContractId = contract.id;
      state.selectedActionIds.clear();
      refs.rankMessage.textContent = "";
      refs.resolutionBox.textContent = "이 회사 의뢰에 맞는 체크 항목을 고른 뒤 제출하라.";
      renderContractBoard();
      renderChecklist();
      renderIncident();
    });

    refs.contractBoard.appendChild(fragment);
  });
}

function renderChecklist() {
  refs.checklistGrid.innerHTML = "";

  state.checklist.forEach((item) => {
    const fragment = refs.checklistTemplate.content.cloneNode(true);
    const input = fragment.querySelector(".check-input");
    const label = fragment.querySelector(".check-item");

    fragment.querySelector(".check-label").textContent = item.label;
    fragment.querySelector(".check-kind").textContent = item.kind;
    fragment.querySelector(".check-summary").textContent = item.summary;

    input.value = item.id;
    input.checked = state.selectedActionIds.has(item.id);
    input.disabled = state.processing || !selectedContract();
    label.classList.toggle("checked", input.checked);

    input.addEventListener("change", () => {
      if (input.checked && state.selectedActionIds.size >= state.maxSelections) {
        input.checked = false;
        refs.resolutionBox.textContent = `한 사건에서 체크할 수 있는 항목은 최대 ${state.maxSelections}개다. 핵심 조치와 보조 조치를 추려서 제출하라.`;
        return;
      }

      if (input.checked) state.selectedActionIds.add(item.id);
      else state.selectedActionIds.delete(item.id);

      label.classList.toggle("checked", input.checked);
      renderHint();
      updateSubmitState();
    });

    refs.checklistGrid.appendChild(fragment);
  });
}

function updateSubmitState() {
  refs.resolveButton.disabled = state.processing || !selectedContract() || state.selectedActionIds.size === 0;
}

function renderHint() {
  const contract = selectedContract();
  if (!contract) {
    refs.budgetHint.textContent = "회사를 먼저 선택하라";
    return;
  }

  refs.budgetHint.textContent = `기본 보상 ${contract.reward} 코인 · 체크 ${state.selectedActionIds.size}/${state.maxSelections}`;
}

function threatClass(level) {
  if (level === "매우 높음" || level === "높음") return "threat-high";
  if (level === "중간") return "threat-mid";
  return "threat-low";
}

function renderEmptyIncident() {
  refs.threatBadge.className = "threat-badge threat-low";
  refs.threatBadge.textContent = "대기";
  refs.incidentName.textContent = "회사를 선택하라";
  refs.incidentBrief.textContent = "회사 리스트에서 의뢰를 고르면 아래에 사건 정보가 열린다.";
  refs.clientName.textContent = "-";
  refs.incidentTarget.textContent = "-";
  refs.contractReward.textContent = "-";
  refs.symptomList.innerHTML = "";
  refs.consequenceList.innerHTML = "";
  refs.goalText.textContent = "회사를 선택하면 사건의 징후, 표적, 방치 시 결과가 표시된다.";
  refs.progressBar.style.width = "0%";
  refs.processingStatus.textContent = "선택 조합에 따라 처리 시간은 짧게 계산되며 최대 5초를 넘지 않는다.";
  refs.summaryPanel.classList.toggle("hidden", !state.gameOver);
  renderAdvisors("");
  renderHint();
  updateSubmitState();
}

function renderIncident() {
  const contract = selectedContract();
  if (!contract) {
    renderEmptyIncident();
    return;
  }

  refs.summaryPanel.classList.add("hidden");
  refs.threatBadge.className = `threat-badge ${threatClass(contract.threatLevel)}`;
  refs.threatBadge.textContent = `위험도 ${contract.threatLevel}`;
  refs.incidentName.textContent = contract.name;
  refs.incidentBrief.textContent = contract.brief;
  refs.clientName.textContent = contract.client;
  refs.incidentTarget.textContent = contract.target;
  refs.contractReward.textContent = `${contract.reward} 코인`;
  refs.symptomList.innerHTML = contract.symptoms.map((item) => `<li>${item}</li>`).join("");
  refs.consequenceList.innerHTML = contract.consequences.map((item) => `<li>${item}</li>`).join("");
  refs.goalText.textContent = `${contract.client} 의뢰의 상황을 읽고 고정 체크리스트에서 필요한 대응을 직접 골라 제출하라.`;
  renderAdvisors(contract.advisorId);
  renderHint();
  updateSubmitState();
}

function evaluateSubmission(contract) {
  const selectedIds = [...state.selectedActionIds];
  const requiredHits = contract.requiredActions.filter((id) => state.selectedActionIds.has(id)).length;
  const helpfulHits = (contract.helpfulActions || []).filter((id) => state.selectedActionIds.has(id)).length;
  const harmfulHits = (contract.harmfulActions || []).filter((id) => state.selectedActionIds.has(id)).length;
  const requiredMisses = contract.requiredActions.length - requiredHits;

  state.trust = clamp(state.trust + (contract.impact?.trust ?? 0));
  state.ops = clamp(state.ops + (contract.impact?.ops ?? 0));

  let earnedCoins = Math.max(4, Math.floor(contract.reward * 0.2));
  let outcome = "부분 대응";
  let reportText = contract.report.partial;

  if (requiredMisses === 0 && harmfulHits === 0) {
    earnedCoins = contract.reward + helpfulHits * 3;
    state.trust = clamp(state.trust + 6 + helpfulHits);
    state.ops = clamp(state.ops + 4);
    outcome = helpfulHits >= 1 ? "정밀 대응 성공" : "핵심 대응 성공";
    reportText = contract.report.success;
  } else if (harmfulHits > 0) {
    earnedCoins = Math.max(0, Math.floor(contract.reward * 0.1) - harmfulHits * 2);
    state.trust = clamp(state.trust - 10 - harmfulHits * 2);
    state.ops = clamp(state.ops - 8 - requiredMisses * 2);
    outcome = "오판으로 피해 확대";
    reportText = contract.report.failure;
  } else if (requiredHits > 0) {
    earnedCoins = Math.max(6, Math.floor(contract.reward * 0.45) + helpfulHits * 2);
    state.trust = clamp(state.trust - 2 + helpfulHits);
    state.ops = clamp(state.ops - Math.max(0, requiredMisses * 3 - helpfulHits));
    outcome = "부분 진압";
    reportText = contract.report.partial;
  } else {
    earnedCoins = Math.max(0, Math.floor(contract.reward * 0.08));
    state.trust = clamp(state.trust - 12);
    state.ops = clamp(state.ops - 11);
    outcome = "핵심 대응 실패";
    reportText = contract.report.failure;
  }

  if (selectedIds.includes("customer-support-surge")) state.trust = clamp(state.trust + 2);
  if (selectedIds.includes("public-briefing") && harmfulHits === 0) state.trust = clamp(state.trust + 1);
  if (selectedIds.includes("full-blackout")) state.ops = clamp(state.ops - 5);

  state.coins += Math.max(0, earnedCoins);

  return {
    earnedCoins,
    outcome,
    requiredHits,
    helpfulHits,
    harmfulHits,
    reportText
  };
}

function processingDurationFor(contract) {
  const requiredSelected = contract.requiredActions.filter((id) => state.selectedActionIds.has(id)).length;
  const helpfulSelected = (contract.helpfulActions || []).filter((id) => state.selectedActionIds.has(id)).length;
  const duration = MIN_PROCESS_MS + requiredSelected * 1200 + helpfulSelected * 700 + state.selectedActionIds.size * 300;
  return Math.min(MAX_PROCESS_MS, duration);
}

function finishProcessing() {
  const contract = selectedContract();
  if (!contract) return;

  const result = evaluateSubmission(contract);
  contract.completed = true;
  state.completedContracts += 1;
  state.selectedContractId = "";
  state.selectedActionIds.clear();
  state.processing = false;
  refs.progressBar.style.width = "0%";

  const message = `${contract.client} 계약 처리 완료. ${result.outcome}. 보상 ${result.earnedCoins} 코인. 핵심 ${result.requiredHits}/${contract.requiredActions.length}, 보조 적중 ${result.helpfulHits}, 오판 패턴 ${result.harmfulHits}. ${result.reportText}`;
  refs.processingStatus.textContent = "처리가 끝났다. 다음 회사 의뢰를 선택하라.";
  refs.resolutionBox.textContent = message;

  state.timeline.unshift({
    client: contract.client,
    text: `${contract.name} · ${result.outcome} · ${result.earnedCoins} 코인`
  });

  if (state.completedContracts >= CONTRACT_TARGET) {
    state.gameOver = true;
    refs.summaryPanel.classList.remove("hidden");
    refs.summaryTitle.textContent =
      state.coins >= 260 ? "최상위 계약자 등급" :
      state.coins >= 180 ? "상위 계약자 등급" :
      "계약 시즌 완료";
    refs.summaryBody.textContent = `16개 의뢰를 모두 완료했다. 최종 코인 ${state.coins}, 신뢰도 ${state.trust}, 운영 안정성 ${state.ops}.`;
  }

  updateStats();
  renderTimeline();
  renderRankPanel();
  renderContractBoard();
  renderChecklist();
  renderIncident();
}

function startProcessing() {
  const contract = selectedContract();
  if (!contract || state.processing || state.selectedActionIds.size === 0) return;

  state.processing = true;
  state.processingDurationMs = processingDurationFor(contract);
  state.processingStartedAt = Date.now();
  refs.resolveButton.disabled = true;
  refs.resolutionBox.textContent = `${contract.client} 의뢰를 처리 중이다. 선택한 핵심·보조 조합을 기준으로 결과를 계산한다.`;
  refs.processingStatus.textContent = `${contract.client} 계약 처리 중... 약 ${(state.processingDurationMs / 1000).toFixed(1)}초가 소요된다.`;

  const tick = () => {
    const elapsed = Date.now() - state.processingStartedAt;
    const progress = clamp((elapsed / state.processingDurationMs) * 100);
    refs.progressBar.style.width = `${progress}%`;

    if (elapsed >= state.processingDurationMs) {
      clearInterval(state.processingTimer);
      state.processingTimer = null;
      finishProcessing();
    }
  };

  renderChecklist();
  tick();
  state.processingTimer = setInterval(tick, 100);
}

function resetRun() {
  if (state.processingTimer) {
    clearInterval(state.processingTimer);
    state.processingTimer = null;
  }

  state.selectedContractId = "";
  state.selectedActionIds.clear();
  state.processing = false;
  state.processingDurationMs = MIN_PROCESS_MS;
  state.completedContracts = 0;
  state.coins = 0;
  state.trust = 81;
  state.ops = 83;
  state.timeline = [];
  state.gameOver = false;

  refs.progressBar.style.width = "0%";
  refs.processingStatus.textContent = "선택 조합에 따라 처리 시간은 짧게 계산되며 최대 5초를 넘지 않는다.";
  refs.resolutionBox.textContent = "회사를 선택하고 체크 항목을 고르면 결과가 여기 표시된다.";
  refs.summaryPanel.classList.add("hidden");
  refs.rankMessage.textContent = "";

  updateStats();
  renderAdvisors();
  renderTimeline();
  renderRankPanel();
  renderContractBoard();
  renderChecklist();
  renderIncident();
}

async function loadGame() {
  const data = await api("/game-data");
  state.contracts = createContracts(data.incidents);
  state.checklist = data.checklist;
  state.advisors = data.advisors;
  state.goal = data.goal;
  state.maxSelections = data.maxSelections || 3;

  refs.playerName.textContent = state.currentUser;
  refs.scenarioMeta.textContent = `${data.subtitle} · ${data.company}`;
  refs.campaignTitle.textContent = data.campaignTitle;
  refs.companyName.textContent = data.company;
  refs.campaignGoal.textContent = `${data.goal} 체크 항목은 최대 ${state.maxSelections}개까지만 고를 수 있다.`;

  resetRun();
  showGame();
}

function handleSignup(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const displayName = String(form.get("displayName") || "").trim();
  const username = String(form.get("username") || "").trim();
  const password = String(form.get("password") || "").trim();

  if (displayName.length < 2 || username.length < 3 || password.length < 4) {
    setAuthMessage("표시 이름 2자, 아이디 3자, 비밀번호 4자 이상으로 입력하라.");
    return;
  }

  const users = readUsers();
  if (users.some((user) => user.username === username)) {
    setAuthMessage("이미 존재하는 아이디다.");
    return;
  }

  users.push({ displayName, username, password });
  writeUsers(users);
  state.currentUser = displayName;
  localStorage.setItem(SESSION_KEY, displayName);

  loadGame().catch(() => {
    setAuthMessage("게임 데이터를 불러오지 못했다. Python API가 실행 중인지 확인하라.");
  });
}

function handleLogin(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const username = String(form.get("username") || "").trim();
  const password = String(form.get("password") || "").trim();
  const user = readUsers().find((item) => item.username === username && item.password === password);

  if (!user) {
    setAuthMessage("아이디 또는 비밀번호가 올바르지 않다.");
    return;
  }

  state.currentUser = user.displayName;
  localStorage.setItem(SESSION_KEY, user.displayName);

  loadGame().catch(() => {
    setAuthMessage("게임 데이터를 불러오지 못했다. Python API가 실행 중인지 확인하라.");
  });
}

function handleLogout() {
  if (state.processingTimer) {
    clearInterval(state.processingTimer);
    state.processingTimer = null;
  }
  localStorage.removeItem(SESSION_KEY);
  state.currentUser = "";
  showAuth();
  switchAuthTab("login");
}

function handleRankSubmit(event) {
  event.preventDefault();
  if (state.completedContracts < CONTRACT_TARGET) return;

  const name = refs.rankNameInput.value.trim() || state.currentUser || "플레이어";
  const entries = readLeaderboard();
  entries.push({
    name,
    coins: state.coins,
    createdAt: new Date().toISOString()
  });
  writeLeaderboard(entries);
  refs.rankMessage.textContent = `${name} 이름으로 ${state.coins} 코인 기록을 등록했다.`;
  renderLeaderboard();
}

async function bootstrap() {
  refs.signupForm.addEventListener("submit", handleSignup);
  refs.loginForm.addEventListener("submit", handleLogin);
  refs.rankForm.addEventListener("submit", handleRankSubmit);
  refs.showLoginTab.addEventListener("click", () => switchAuthTab("login"));
  refs.showSignupTab.addEventListener("click", () => switchAuthTab("signup"));
  refs.helpButton.addEventListener("click", openHelp);
  refs.closeHelpButton.addEventListener("click", closeHelp);
  refs.helpModal.addEventListener("click", (event) => {
    if (event.target === refs.helpModal) closeHelp();
  });
  refs.logoutButton.addEventListener("click", handleLogout);
  refs.refreshContractsButton.addEventListener("click", () => {
    loadGame().catch(() => {
      refs.resolutionBox.textContent = "의뢰 세트를 새로 불러오지 못했다.";
    });
  });
  refs.resolveButton.addEventListener("click", startProcessing);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeHelp();
  });

  switchAuthTab("login");
  renderLeaderboard();

  if (!state.currentUser) {
    showAuth();
    return;
  }

  try {
    await loadGame();
  } catch {
    localStorage.removeItem(SESSION_KEY);
    state.currentUser = "";
    setAuthMessage("게임 데이터를 불러오지 못했다. Python API가 실행 중인지 확인하라.");
    showAuth();
  }
}

bootstrap();
