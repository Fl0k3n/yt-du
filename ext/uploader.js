console.log('uploader runnign');
const DOM_TIMEOUT = 250; //ms
const MAX_RETRIES = 15; // if query selector fails after this error is raised

async function sleep(time_ms) {
    return new Promise((res, _) => setTimeout(res, time_ms));
}

async function tryQS(selector, parent = document) {
    for (let i = 0; i < MAX_RETRIES; i++) {
        const res = parent.querySelector(selector);
        if (res != null)
            return new Promise((resolve, _) => resolve(res));
        await sleep(DOM_TIMEOUT);
    }

    return new Promise((_, rej) => rej(`Failed to select: ${selector}`));
}


async function setSettings(vis = 'PRIVATE') {
    try {
        const box = await tryQS('#row-container.row-selected');
        box.querySelector('#video-thumbnail-container').click();
        const kids = await tryQS('#made-for-kids-group  [name="MADE_FOR_KIDS"]');
        kids.click();
        const btn = document.querySelector('#next-button');
        btn.click(); // details
        btn.click(); //video elements
        btn.click(); //checks
        const radios = await tryQS(`#privacy-radios [name="${vis}"]`);
        radios.click();

        document.querySelector('#done-button').click();
        box.classList.remove('row-selected');

        setTimeout(async function retry() {
            const d1 = document.querySelector('ytcp-dialog.ytcp-uploads-still-processing-dialog');
            if (d1 != null) {
                d1.querySelector('#close-button').click();
            }
            const d2 = document.querySelector('ytcp-uploads-dialog');

            if (d1 == null && d2 == null)
                await setSettings(vis);
            else
                setTimeout(retry, 100);
        }, 100);
    }
    catch (err) {
        console.log(err);
        return;
    }
}


async function addButton() {
    const parent = await tryQS('#video-list');

    const style = document.createElement('style');
    style.innerHTML = `
        #_my-upload-btn {
            position: fixed;
            bottom: 50px;
            right: 50px;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            z-index: 1000000;
        }

        #_my-upload-btn:hover {
            opacity: 0.9;
            cursor: pointer !important;
        }
    `;

    document.querySelector('head').appendChild(style);

    const btn = document.createElement('button');
    btn.id = '_my-upload-btn';
    parent.appendChild(btn);

    btn.textContent = 'Fast upload';
    btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        await setSettings();
    });
}


addButton().then(() => null);