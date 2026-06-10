const API = "";

let allTeams        = [];
let allPlayoffTeams = [];


// ─────────────────────────────────────────
// Tab switching
// ─────────────────────────────────────────

function switchTab(name) {

    document.querySelectorAll(".panel").forEach(
        p => p.classList.remove("active")
    );

    document.querySelectorAll(".tab-btn").forEach(
        b => b.classList.remove("active")
    );

    document.getElementById(`panel-${name}`)
        .classList.add("active");

    document.getElementById(`btn-${name}`)
        .classList.add("active");
}


// ─────────────────────────────────────────
// Shared utilities
// ─────────────────────────────────────────

function populateSelect(id, options) {

    const select   = document.getElementById(id);
    const previous = select.value;

    select.innerHTML = "";

    options.forEach(opt => {
        const el   = document.createElement("option");
        el.value   = opt;
        el.text    = opt;
        select.appendChild(el);
    });

    if (options.includes(previous)) {
        select.value = previous;
    }
}

function buildProbBar(probA, probB) {
    return `
        <div class="prob-bar">
            <div class="prob-bar-a" style="width:${probA}%">
                ${probA}%
            </div>
            <div class="prob-bar-b" style="width:${probB}%">
                ${probB}%
            </div>
        </div>
    `;
}

function buildFactorRows(topFactors) {
    return topFactors.map(f => `
        <div class="factor">
            <span class="factor-stat">${f.stat}</span>
            <span class="factor-value">+${f.value}</span>
        </div>
    `).join("");
}


// ─────────────────────────────────────────
// Single game
// ─────────────────────────────────────────

function filterTeams(side) {

    const year      = document.getElementById(`year${side}`).value;
    const validTeams = allTeams
        .filter(t => t.startsWith(year + " | "))
        .map(t => t.split(" | ")[1])
        .sort();

    populateSelect(`team${side}`, validTeams);
}


async function loadTeams() {

    const response = await fetch(`${API}/teams`);
    allTeams       = await response.json();

    const years = [
        ...new Set(allTeams.map(t => t.split(" | ")[0]))
    ].sort().reverse();

    populateSelect("yearA", years);
    populateSelect("yearB", years);

    filterTeams("A");
    filterTeams("B");

    document.getElementById("yearA")
        .addEventListener("change", () => filterTeams("A"));

    document.getElementById("yearB")
        .addEventListener("change", () => filterTeams("B"));
}


async function predictMatchup() {

    const yearA = document.getElementById("yearA").value;
    const teamA = document.getElementById("teamA").value;
    const yearB = document.getElementById("yearB").value;
    const teamB = document.getElementById("teamB").value;

    const displayA = `${yearA} | ${teamA}`;
    const displayB = `${yearB} | ${teamB}`;

    const btn = document.getElementById("btn-predict");
    btn.textContent = "Simulating 10,000 games…";
    btn.disabled    = true;

    try {

        const response = await fetch(`${API}/predict`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ team_a: displayA, team_b: displayB })
        });

        if (!response.ok) {
            const err = await response.json();
            document.getElementById("result-single").innerHTML =
                `<p style="color:#e74c3c;">
                    Error: ${err.error || "Something went wrong"}
                </p>`;
            return;
        }

        const data = await response.json();

        const probA     = (data.team_a_win_probability * 100).toFixed(1);
        const probB     = (data.team_b_win_probability * 100).toFixed(1);
        const winnerIsA = data.winner === displayA;
        const winnerShort = data.winner.split(" | ")[1];

        document.getElementById("result-single").innerHTML = `

            <div class="result-row">
                <div class="result-card ${winnerIsA ? "winner" : ""}">
                    <h2>${displayA}</h2>
                    <div class="prob">${probA}%</div>
                    <div class="sim-count">
                        ${data.team_a_sim_wins.toLocaleString()} /
                        ${data.total_simulations.toLocaleString()} wins
                    </div>
                </div>
                <div class="result-card ${!winnerIsA ? "winner" : ""}">
                    <h2>${displayB}</h2>
                    <div class="prob">${probB}%</div>
                    <div class="sim-count">
                        ${data.team_b_sim_wins.toLocaleString()} /
                        ${data.total_simulations.toLocaleString()} wins
                    </div>
                </div>
            </div>

            <div class="prob-bar-wrap">
                ${buildProbBar(probA, probB)}
                <div class="prob-bar-labels">
                    <span>${displayA}</span>
                    <span>${displayB}</span>
                </div>
            </div>

            <div class="factors">
                <h3>Why ${winnerShort} wins</h3>
                ${buildFactorRows(data.top_factors)}
            </div>
        `;

    } finally {
        btn.textContent = "Simulate Matchup";
        btn.disabled    = false;
    }
}


// ─────────────────────────────────────────
// Playoff series
// ─────────────────────────────────────────

function filterPlayoffTeams(side) {

    const year      = document.getElementById(`playoffYear${side}`).value;
    const validTeams = allPlayoffTeams
        .filter(t => t.startsWith(year + " | "))
        .map(t => t.split(" | ")[1])
        .sort();

    populateSelect(`playoffTeam${side}`, validTeams);
}


async function loadPlayoffTeams() {

    const response  = await fetch(`${API}/playoff_teams`);
    allPlayoffTeams = await response.json();

    const years = [
        ...new Set(allPlayoffTeams.map(t => t.split(" | ")[0]))
    ].sort().reverse();

    populateSelect("playoffYearA", years);
    populateSelect("playoffYearB", years);

    filterPlayoffTeams("A");
    filterPlayoffTeams("B");

    document.getElementById("playoffYearA")
        .addEventListener("change", () => filterPlayoffTeams("A"));

    document.getElementById("playoffYearB")
        .addEventListener("change", () => filterPlayoffTeams("B"));
}


async function predictSeries() {

    const yearA = document.getElementById("playoffYearA").value;
    const teamA = document.getElementById("playoffTeamA").value;
    const yearB = document.getElementById("playoffYearB").value;
    const teamB = document.getElementById("playoffTeamB").value;

    const displayA = `${yearA} | ${teamA}`;
    const displayB = `${yearB} | ${teamB}`;

    const btn = document.getElementById("btn-series-sim");
    btn.textContent = "Simulating 10,000 series…";
    btn.disabled    = true;

    try {

        const response = await fetch(`${API}/predict_series`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ team_a: displayA, team_b: displayB })
        });

        if (!response.ok) {
            const err = await response.json();
            document.getElementById("result-series").innerHTML =
                `<p style="color:#e74c3c;">
                    Error: ${err.error || "Something went wrong"}
                </p>`;
            return;
        }

        const data = await response.json();

        const winnerIsA   = data.winner === displayA;
        const winnerShort = data.winner.split(" | ")[1];

        // ── Series length bars ────────────────────

        const maxLenPct = Math.max(
            ...Object.values(data.length_distribution)
        );

        const lengthBars = Object.entries(data.length_distribution)
            .map(([games, pct]) => `
                <div class="dist-row">
                    <span class="dist-label">${games} games</span>
                    <div class="dist-bar-container">
                        <div class="dist-bar"
                             style="width:${(pct / maxLenPct * 100).toFixed(1)}%">
                        </div>
                    </div>
                    <span class="dist-pct">${pct}%</span>
                </div>
            `)
            .join("");

        // ── Series outcome bars ───────────────────

        const outcomes    = Object.entries(data.series_outcomes).slice(0, 6);
        const maxOutPct   = Math.max(...outcomes.map(([, v]) => v));

        const outcomeRows = outcomes.map(([outcome, pct]) => {

            const [wA, wB]    = outcome.split("-").map(Number);
            const outcomeTeam = wA === 4 ? teamA : teamB;
            const wWins       = wA === 4 ? wA : wB;
            const lWins       = wA === 4 ? wB : wA;

            return `
                <div class="outcome-row">
                    <span class="outcome-winner"
                          title="${outcomeTeam}">
                        ${outcomeTeam.split(" ").slice(-1)[0]}
                    </span>
                    <span class="outcome-result">${wWins}-${lWins}</span>
                    <div class="outcome-bar-container">
                        <div class="outcome-bar"
                             style="width:${(pct / maxOutPct * 100).toFixed(1)}%">
                        </div>
                    </div>
                    <span class="outcome-pct">${pct}%</span>
                </div>
            `;
        }).join("");

        document.getElementById("result-series").innerHTML = `

            <div class="result-row">
                <div class="result-card ${winnerIsA ? "winner" : ""}">
                    <h2>${displayA}</h2>
                    <div class="prob">${data.series_win_prob_a}%</div>
                    <div class="sim-count">Series win probability</div>
                </div>
                <div class="result-card ${!winnerIsA ? "winner" : ""}">
                    <h2>${displayB}</h2>
                    <div class="prob">${data.series_win_prob_b}%</div>
                    <div class="sim-count">Series win probability</div>
                </div>
            </div>

            <div class="prob-bar-wrap">
                ${buildProbBar(data.series_win_prob_a, data.series_win_prob_b)}
                <div class="prob-bar-labels">
                    <span>${displayA}</span>
                    <span>${displayB}</span>
                </div>
            </div>

            <div class="series-stats-row">
                <div class="stat-badge">
                    <div class="stat-badge-label">Expected Games</div>
                    <div class="stat-badge-value">${data.expected_games}</div>
                </div>
                <div class="stat-badge">
                    <div class="stat-badge-label">Per-Game Win % (${teamA.split(" ").slice(-1)[0]})</div>
                    <div class="stat-badge-value">${data.game_win_prob_a}%</div>
                </div>
                <div class="stat-badge">
                    <div class="stat-badge-label">Simulations Run</div>
                    <div class="stat-badge-value">
                        ${data.total_simulations.toLocaleString()}
                    </div>
                </div>
            </div>

            <div class="series-charts-row">
                <div class="series-chart-panel">
                    <h3>Series Length</h3>
                    ${lengthBars}
                </div>
                <div class="series-chart-panel">
                    <h3>Most Likely Outcomes</h3>
                    ${outcomeRows}
                </div>
            </div>

            <div class="factors">
                <h3>Why ${winnerShort} wins</h3>
                ${buildFactorRows(data.top_factors)}
            </div>
        `;

    } finally {
        btn.textContent = "Simulate Series";
        btn.disabled    = false;
    }
}


// ─────────────────────────────────────────
// Init
// ─────────────────────────────────────────

loadTeams();
loadPlayoffTeams();