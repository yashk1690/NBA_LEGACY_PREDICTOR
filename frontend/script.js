// Flask is now serving this file, so use relative URLs
const API = "";

let allTeams = [];


function populateSelect(id, options) {

    const select = document.getElementById(id);
    const previous = select.value;

    select.innerHTML = "";

    options.forEach(opt => {
        const el = document.createElement("option");
        el.value = opt;
        el.text = opt;
        select.appendChild(el);
    });

    if (options.includes(previous)) {
        select.value = previous;
    }
}


function filterTeams(side) {

    const year = document.getElementById(
        `year${side}`
    ).value;

    const validTeams = allTeams
        .filter(t => t.startsWith(year + " | "))
        .map(t => t.split(" | ")[1])
        .sort();

    populateSelect(`team${side}`, validTeams);
}


async function loadTeams() {

    const response = await fetch(`${API}/teams`);
    allTeams = await response.json();

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

    const btn = document.querySelector("button");
    btn.textContent = "Simulating...";
    btn.disabled = true;

    try {

        const response = await fetch(
            `${API}/predict`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    team_a: displayA,
                    team_b: displayB
                })
            }
        );

        if (!response.ok) {
            const err = await response.json();
            document.getElementById("result").innerHTML =
                `<p style="color:#e74c3c;">
                    Error: ${err.error || "Something went wrong"}
                </p>`;
            return;
        }

        const data = await response.json();

        const probA = (
            data.team_a_win_probability * 100
        ).toFixed(1);

        const probB = (
            data.team_b_win_probability * 100
        ).toFixed(1);

        const winnerIsA = data.winner === displayA;
        const winnerShort = data.winner.split(" | ")[1];

        // Build the factor rows (all from the winning team)
        const factorRows = data.top_factors
            .map(f => `
                <div class="factor">
                    <span class="factor-stat">${f.stat}</span>
                    <span class="factor-value">+${f.value}</span>
                </div>
            `)
            .join("");

        document.getElementById("result").innerHTML = `

            <div class="result-row">

                <div class="result-card ${winnerIsA ? "winner" : ""}">
                    <h2>${displayA}</h2>
                    <div class="prob">${probA}%</div>
                </div>

                <div class="result-card ${!winnerIsA ? "winner" : ""}">
                    <h2>${displayB}</h2>
                    <div class="prob">${probB}%</div>
                </div>

            </div>

            <div class="prob-bar-wrap">
                <div class="prob-bar">
                    <div class="prob-bar-a" style="width:${probA}%">
                        ${probA}%
                    </div>
                    <div class="prob-bar-b" style="width:${probB}%">
                        ${probB}%
                    </div>
                </div>
                <div class="prob-bar-labels">
                    <span>${displayA}</span>
                    <span>${displayB}</span>
                </div>
            </div>

            <div class="factors">
                <h3>Why ${winnerShort} wins</h3>
                ${factorRows}
            </div>

        `;

    } finally {
        btn.textContent = "Simulate Matchup";
        btn.disabled = false;
    }
}


loadTeams();