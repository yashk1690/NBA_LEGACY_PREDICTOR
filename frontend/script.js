const API = "http://127.0.0.1:5000";

// All display names from the API e.g. "2022-23 | Los Angeles Lakers"
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

    // Restore previous selection if it's still valid
    if (options.includes(previous)) {
        select.value = previous;
    }
}


function filterTeams(side) {

    const year = document.getElementById(`year${side}`).value;

    const validTeams = allTeams
        .filter(t => t.startsWith(year + " | "))
        .map(t => t.split(" | ")[1])
        .sort();

    populateSelect(`team${side}`, validTeams);
}


async function loadTeams() {

    const response = await fetch(`${API}/teams`);
    allTeams = await response.json();

    // Extract unique years, most recent first
    const years = [
        ...new Set(allTeams.map(t => t.split(" | ")[0]))
    ].sort().reverse();

    populateSelect("yearA", years);
    populateSelect("yearB", years);

    // Populate teams for initial year selection
    filterTeams("A");
    filterTeams("B");

    // Cascade: re-filter teams when year changes
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

    // Reconstruct display names the API expects
    const displayA = `${yearA} | ${teamA}`;
    const displayB = `${yearB} | ${teamB}`;

    const response = await fetch(
        `${API}/predict`,
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                team_a: displayA,
                team_b: displayB
            })
        }
    );

    const data = await response.json();

    const probA = (data.team_a_win_probability * 100).toFixed(1);
    const probB = (data.team_b_win_probability * 100).toFixed(1);

    document.getElementById("result").innerHTML = `
        <div class="result-row">
            <div class="result-card">
                <h2>${displayA}</h2>
                <div class="prob">${probA}%</div>
            </div>
            <div class="result-card">
                <h2>${displayB}</h2>
                <div class="prob">${probB}%</div>
            </div>
        </div>
    `;
}


loadTeams();