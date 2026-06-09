const API =
    "http://127.0.0.1:5000";


async function loadTeams(){

    const response =
        await fetch(
            `${API}/teams`
        );

    const teams =
        await response.json();

    const teamA =
        document.getElementById(
            "teamA"
        );

    const teamB =
        document.getElementById(
            "teamB"
        );

    teams.forEach(team => {

        let optionA =
            document.createElement(
                "option"
            );

        optionA.value = team;
        optionA.text = team;

        teamA.appendChild(optionA);

        let optionB =
            document.createElement(
                "option"
            );

        optionB.value = team;
        optionB.text = team;

        teamB.appendChild(optionB);

    });
}


async function predictMatchup(){

    const teamA =
        document.getElementById(
            "teamA"
        ).value;

    const teamB =
        document.getElementById(
            "teamB"
        ).value;

    const response =
        await fetch(
            `${API}/predict`,
            {
                method:"POST",

                headers:{
                    "Content-Type":
                    "application/json"
                },

                body:JSON.stringify({
                    team_a:teamA,
                    team_b:teamB
                })
            }
        );

    const data =
        await response.json();

    document.getElementById(
        "result"
    ).innerHTML = `

    <h2>${data.team_a}</h2>

    <p>
        Win Probability:
        ${(data.team_a_win_probability * 100).toFixed(2)}%
    </p>

    <h2>${data.team_b}</h2>

    <p>
        Win Probability:
        ${(data.team_b_win_probability * 100).toFixed(2)}%
    </p>

    `;
}


loadTeams();