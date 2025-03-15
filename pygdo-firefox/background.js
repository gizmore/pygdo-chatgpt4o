chrome.runtime.onInstalled.addListener(() => {
    console.log("ChatGPT to PyGDO Bridge installed.");
});

chrome.runtime.onStartup.addListener(() => {
    console.log("ChatGPT to PyGDO Bridge started.");
});
