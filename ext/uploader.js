console.log('uploader runnign');
const DOM_TIMEOUT = 250; //ms
const MAX_RETRIES = 15; // if query selector fails after this error is raised

async function sleep(time_ms) {
    return new Promise((res, _) => setTimeout(res, time_ms));
}

async function tryQS(selector) {
    for (let i = 0; i < MAX_RETRIES; i++) {
        const res = document.querySelector(selector);
        if (res != null)
            return new Promise((resolve, _) => resolve(res));
        await sleep(DOM_TIMEOUT);
    }

    return new Promise((_, rej) => rej(`Failed to select: ${selector}`));
}

async function main() {
    const btn = await tryQS('#upload-button');
    btn.click();
    const sf = await tryQS('#select-files-button');
    sf.click();
}

main().then(() => console.log('done'));