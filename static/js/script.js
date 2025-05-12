var count = 0;
let speech = new SpeechSynthesisUtterance();

document.querySelector("#speak-button").addEventListener("click", () => {
    count++;
    speech.text = document.getElementById("speak-text").innerText;

    speech.rate = 1;

    console.log(speech.text);
    console.log(count);

    if (count % 2 == 0) {
        window.speechSynthesis.cancel();
    } else {
        window.speechSynthesis.speak(speech);
    }
});

function fillChatInput(question) {
    document.querySelector("input[name='prompt']").value = question;
}

function showChatHistory(question, answer) {
    let messagesContainer = document.querySelector(".messages");
    let backButton = document.getElementById("back-to-chat");

    messagesContainer.innerHTML = "";

    backButton.style.display = "block";

    let userMessage = document.createElement("div");
    userMessage.classList.add("message", "user-message");
    userMessage.innerHTML = `<b>You:</b> ${question}`;
    
    let botMessage = document.createElement("div");
    botMessage.classList.add("message", "bot-message");
    botMessage.innerHTML = `<b>Bot:</b> ${answer}`;
    
    messagesContainer.appendChild(userMessage);
    messagesContainer.appendChild(botMessage);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showMainChat() {
    let messagesContainer = document.querySelector(".messages");
    let backButton = document.getElementById("back-to-chat");

    messagesContainer.innerHTML = "";

    backButton.style.display = "none";

    try {
        let chatDataDiv = document.getElementById("chat-data");
        let chatHistory = JSON.parse(chatDataDiv.textContent || "[]");

        if (chatHistory.length === 0) {
            messagesContainer.innerHTML = "<p style='text-align: center; color: gray;'>No chat history found.</p>";
            return;
        }

        chatHistory.forEach(content => {
            let userMessage = document.createElement("div");
            userMessage.classList.add("message", "user-message");
            userMessage.innerHTML = `<b>You:</b> ${content.prompt}`;

            let botMessage = document.createElement("div");
            botMessage.classList.add("message", "bot-message");
            botMessage.innerHTML = `<b>Bot:</b> ${content.output}`;

            messagesContainer.appendChild(userMessage);
            messagesContainer.appendChild(botMessage);
        });

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (error) {
        console.error("Error loading chat history:", error);
    }
}

function switchTab(tab) {
    let quizBtn = document.getElementById("quiz-btn");
    let gradesBtn = document.getElementById("grades-btn");

    if (tab === "quiz") {
        quizBtn.classList.add("active");
        gradesBtn.classList.remove("active");
    } else {
        quizBtn.classList.remove("active");
        gradesBtn.classList.add("active");
    }
}
