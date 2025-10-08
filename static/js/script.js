document.getElementById('genForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        length: document.getElementById('length').value,
        uppercase: document.getElementById('upper').checked,
        lowercase: document.getElementById('lower').checked,
        numbers: document.getElementById('nums').checked,
        symbols: document.getElementById('syms').checked
    };
    const res = await fetch('/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    const json = await res.json();
    const div = document.getElementById('result');
    if (json.error) {
        div.textContent = json.error;
    } else {
        div.innerHTML = json.passwords.map(p => `${p.password} — ${p.score_percent}%`).join('<br>');
    }
});
