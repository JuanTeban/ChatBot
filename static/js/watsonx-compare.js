document.getElementById("compare-form").addEventListener("submit", async e => {
  e.preventDefault();
  const form = e.target;
  const data = new FormData(form);
  const res = await fetch("/watsonx/compare", {
    method: "POST",
    body: data
  });
  const json = await res.json();
  document.getElementById("compare-result").textContent = json.result;
});
