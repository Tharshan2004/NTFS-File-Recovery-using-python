document.getElementById('recoveryForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const formData = new FormData();
    const ntfsImageFile = document.getElementById('ntfsImageFile').files[0];
    const saveFolder = document.getElementById('saveFolder').value;

    formData.append('ntfs_image_file', ntfsImageFile);
    formData.append('save_folder', saveFolder);

    document.getElementById('startRecoveryButton').disabled = true;
    updateProgress(0); // Start progress bar

    try {
        const response = await fetch('/recover_files', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById('filesRecovered').textContent = result.files_recovered;
            document.getElementById('filesSkipped').textContent = result.files_skipped;
            document.getElementById('errors').textContent = result.errors;
            updateProgress(100); // End progress bar
        } else {
            alert('Error during recovery process. Please try again.');
            updateProgress(0); // Reset progress bar on error
        }
    } catch (error) {
        console.error('Recovery failed:', error);
        alert('Error occurred: ' + error.message);
        updateProgress(0); // Reset progress bar on error
    } finally {
        document.getElementById('startRecoveryButton').disabled = false;
    }
});

// Folder selection logic using an input dialog for folders
document.getElementById('selectFolderButton').addEventListener('click', function () {
    window.showDirectoryPicker()
        .then(folderHandle => {
            document.getElementById('saveFolder').value = folderHandle.name;  // Just the folder name, you may modify to get the full path
        })
        .catch(error => {
            console.error('Folder selection failed:', error);
        });
});

// Progress bar update function
function updateProgress(percent) {
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = percent + '%';
}
