async function ask() {
  const res = await fetch("/api/v1/ask", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      kundali_core_id: document.getElementById("kundaliId").value,
      question: document.getElementById("question").value
    })
  })
  document.getElementById("answer").innerText = await res.text()
}
