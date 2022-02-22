let MAX_RETRIES = 10;
const HREFS_CODE = 1; // match with background.js codes
const DOM_TIMEOUT = 250;


async function sleep(time_ms) {
    return new Promise((res, _) => setTimeout(res, time_ms));
}

async function tryQS(selector, all = false, parent = document) {
    for (let i = 0; i < MAX_RETRIES; i++) {
        const res = all ? parent.querySelectorAll(selector) : parent.querySelector(selector);
        if (all ? res.length > 0 : res != null)
            return new Promise((resolve, _) => resolve(res));
        await sleep(DOM_TIMEOUT);
    }

    return new Promise((_, rej) => rej(`Failed to select: ${selector}`));
}


async function redirect() {
    const el = await tryQS('ytd-playlist-sidebar-renderer #thumbnail');
    el.click();
}


async function fetchLinks(req) {
    try {
        const aTags = await tryQS('#items a#wc-endpoint', true);
        const hrefs = [...aTags].map(el => el.href);
        const titles = [...aTags].map(tag => tag.querySelector('span#video-title').getAttribute('title'));
        chrome.runtime.sendMessage({
            ...req, content: {
                hrefs: hrefs,
                titles: titles
            },
            success: true
        });

    } catch (err) {
        chrome.runtime.sendMessage({ ...req, success: false, reason: 'Failed to get playlist links ' + err });
    }
}


async function fetchTitle(req) {
    try {
        const titleTag = await tryQS('.super-title + .title');
        chrome.runtime.sendMessage({
            ...req, content: {
                hrefs: [window.location.href],
                titles: [titleTag.textContent]
            },
            success: true
        });
    } catch (err) {
        chrome.runtime.sendMessage({ ...req, success: false, reason: 'Failed to get title of playlist link ' + err });
    }
}


chrome.runtime.onMessage.addListener(async (req, sender, resp) => {
    if (!req.code)
        return;

    const req_param_re = /(\?|&)v=/;
    if (!req_param_re.test(req.playlist))
        await redirect();

    switch (req.code) {
        case HREFS_CODE:
            if (window.location.href.includes('list='))
                await fetchLinks(req);
            else
                await fetchTitle(req);
            break;
        default:
            chrome.runtime.sendMessage({ ...req, success: false, reason: 'Unsupported task code' });
    }
});