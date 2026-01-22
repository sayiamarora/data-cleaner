async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const status = document.getElementById("status");
  const downloadLink = document.getElementById("downloadLink");
  const reportBox = document.getElementById("reportBox");

  const file = fileInput.files[0];
  if (!file) {
    alert("Please upload a file");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  status.innerText = "Processing your data...";
  reportBox.style.display = "none";
  downloadLink.style.display = "none";

  const response = await fetch("http://127.0.0.1:8000/clean-data", {
    method: "POST",
    body: formData
  });

  const data = await response.json();

  status.innerText = data.message;

  // Download link
  downloadLink.href = "http://127.0.0.1:8000/" + data.download_file;
  downloadLink.innerText = "Download Cleaned File";
  downloadLink.style.display = "block";

  // Show report
  document.getElementById("rowsBefore").innerText = data.report.rows_before;
  document.getElementById("rowsAfter").innerText = data.report.rows_after;
  document.getElementById("duplicatesRemoved").innerText = data.report.duplicates_removed;
  document.getElementById("nullRowsRemoved").innerText = data.report.null_rows_removed;
  document.getElementById("columnsStandardized").innerText = data.report.columns_standardized ? "Yes" : "No";
  document.getElementById("autoDelete").innerText = data.report.file_auto_deleted_in_seconds;

  reportBox.style.display = "block";
}
