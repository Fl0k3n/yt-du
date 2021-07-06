chrome.runtime.onMessage.addListener((req, sender, resp) => {
    /// BRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRr
    // TODO retries with timeout
    // TODO get playlist links
    setTimeout(() => {
        const doc = document.querySelector('#header-contents .ytd-playlist-panel-renderer .index-message');
        chrome.runtime.sendMessage({ ...req, content: doc.textContent });
    }, 3000);
});