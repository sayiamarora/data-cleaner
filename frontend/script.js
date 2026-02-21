async function uploadFile() {
  const file = document.getElementById("fileInput").files[0];
  const status = document.getElementById("status");
  const link = document.getElementById("downloadLink");

  if (!file) return alert("Upload file first");

  const formData = new FormData();
  formData.append("file", file);

  status.innerText = "Processing...";

  const res = await fetch("http://127.0.0.1:8000/clean-data", {
    method: "POST",
    body: formData
  });

  const data = await res.json();

  status.innerText = data.message;

  link.href = "http://127.0.0.1:8000/" + data.download_file;
  link.innerText = "Download Cleaned File";
  link.style.display = "block";

  document.getElementById("rowsBefore").innerText = data.report.rows_before;
  document.getElementById("rowsAfter").innerText = data.report.rows_after;
  document.getElementById("duplicatesRemoved").innerText = data.report.duplicates_removed;
  document.getElementById("nullRowsRemoved").innerText = data.report.null_rows_removed;
  document.getElementById("anomaliesRemoved").innerText = data.report.anomalies_removed;
  document.getElementById("autoDelete").innerText = data.report.file_auto_deleted_in_seconds;

  document.getElementById("reportBox").style.display = "block";
}