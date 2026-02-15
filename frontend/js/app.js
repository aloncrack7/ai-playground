function getSelectedModel() {
    return document.getElementById("modelSelect").value;
}

// handler for generate button
document.getElementById("generateBtn").addEventListener("click", async () => {
    const text = document.getElementById("textBox").value;
    const model = getSelectedModel();

    const response = await fetch("/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: text, model: model })
    });

    const data = await response.json();
    console.log(data);
});

// handler for orthography check

document.getElementById('checkBtn').addEventListener('click', async () => {
    const text = document.getElementById("textBox").value;
    const model = getSelectedModel();

    // TODO: call backend spelling check endpoint
    const response = await fetch("/check", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text: text, model: model })
    });
    const data = await response.json();
    console.log(data);
});