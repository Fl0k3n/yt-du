let MAX_RETRIES = 10;

chrome.runtime.onMessage.addListener((req, sender, resp) => {
    /// BRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRr
    setTimeout(function getEm() {
        // const doc = document.querySelector('#header-contents .ytd-playlist-panel-renderer .index-message'); //size
        const aTags = document.querySelectorAll('#items a#wc-endpoint')

        const hrefs = [...aTags].map(el => el.href);
        if (!hrefs || hrefs.length === 0) {
            if (--MAX_RETRIES > 0)
                setTimeout(getEm, 1000);
            else
                chrome.runtime.sendMessage({ ...req, success: false, reason: 'Failed to get playlist links' });
        }
        else {
            const titles = [...aTags].map(tag => tag.querySelector('span#video-title').getAttribute('title'));
            chrome.runtime.sendMessage({
                ...req, content: {
                    hrefs: hrefs,
                    titles: titles
                }
                , success: true
            });
        }
    }, 1000);
});