console.log('Working');
const PORT = 5555;
const SIZE_CODE = 1;
const connTimeout = 5; // seconds
let retries = 10;
let connEstb = false;
let counter = 0;
class ConnectionHandler {
    constructor(port = 5555, retries = 10, connTimeout = 5) {
        this.PORT = port;
        this.socket = null;
        this.retries = retries;
        this.connEstb = false;
        this.connTimeout = connTimeout;

        this.init();
    }

    init() {
        this.socket = new WebSocket(`ws://127.0.0.1:${this.PORT}`);

        this.socket.addEventListener('error', err => this.onError(err));
        this.socket.addEventListener('open', ev => this.onConnected(ev));
        this.socket.addEventListener('message', e => {
            console.log(`got ${e.data}`);
            const data = JSON.parse(e.data);
            const extractor = new LinkExtractor(this, data['playlists']);

        });
    }

    onError(err) {
        if (!this.connEstb) {
            if (this.retries > 0) {
                console.log(`Failed to connect, retrying...`);
                this.retries--;
                setTimeout(() => this.init(), this.connTimeout * 1000);
            }
            else
                console.log("Failed to connect, aborting.");
        }
        else
            console.log(`Error after connection, aborting`);

        this.socket.close();
        this.socket = null;
    }

    onConnected(ev) {
        this.connEstb = true;
        console.log('connected', ev);
    }

    sendLinks(playlist, links) {
        console.log('in ch send links');
        console.log(playlist);
        console.log(links);

        const payload = {
            playlist: playlist,
            links: links.map((k, v) => {
                return {
                    link: k,
                    dataLinks: v
                };
            })
        };

        this.socket.send(payload);
        console.log('sent');
    }
}


class LinkExtractor {
    constructor(communicationHandler, playlists) {
        this.playlists = playlists;
        this.communicationHandler = communicationHandler;

        this.linksMap = new Map();  // playlist(url) -> {links: Map<link_within_playlist, [DataLink]>, waiting: int}
        this.tabsMap = new Map(); // tabId -> playlist(url)
        this.tabId2Link = new Map(); // tabId -> link (within playlist)

        this.playlists.forEach(playlist => this.getPlaylistItems(playlist));

        chrome.runtime.onMessage.addListener((req, sender, resp) => {
            if (req && req.code === SIZE_CODE) {
                chrome.tabs.remove(sender.tab.id);
                const plSize = this._extractSize(req.content);
                this.linksMap.get(req.playlist).waiting = plSize;
                this._extractLinks(req.playlist, plSize);

                chrome.webRequest.onCompleted.addListener(details => this._linkIntecepted(details), {
                    urls: ["*://*.googlevideo.com/*"]
                });
            }
        });
    }

    getPlaylistItems(playlist) {
        if (this.linksMap.has(playlist)) {
            console.log(`playlist ${playlist} already processed`);
            return;
        }

        this.linksMap.set(playlist, {
            links: new Map(),
            waiting: 0
        });

        chrome.tabs.create({
            active: false,
            url: playlist
        }, tab => {
            chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
                if (tabId === tab.id && info.status === 'complete') {
                    chrome.tabs.onUpdated.removeListener(listener);
                    chrome.tabs.sendMessage(tab.id, { playlist: playlist, code: SIZE_CODE });
                }
            })
        });
    }

    _extractSize(textContent) {
        const re = /\d+\s\/\s(\d+)/;
        const matches = textContent.match(re);
        if (!matches || matches.length < 2)
            throw new Error(`Failed to extract playlist size from ${textContent}`);
        return parseInt(matches[1]);
    }

    _extractLinks(playlistUrl, size) {
        const urls = [];
        for (let i = 1; i <= size; i++)
            urls.push(`${playlistUrl}&index=${i}`);

        urls.forEach(url => {
            chrome.tabs.create({
                active: false,
                url: url
            }, tab => {
                this.tabsMap.set(tab.id, playlistUrl);
                this.tabId2Link.set(tab.id, url);

                const data = this.linksMap.get(playlistUrl);
                data.links.set(url, []);
            });
        });
    }

    _linkIntecepted(details) {
        const { tabId } = details;
        const playlist = this.tabsMap.get(tabId);

        // valid single link intercepted
        if (playlist && this._isValid(details.url)) {
            try {
                console.log(details.url);
                // swap params so single download will suffice
                const clenRe = /clen=(\d+)/;
                const clen = parseInt(details.url.match(clenRe)[1]);

                const rangeRe = /range=0-\d+?/;
                details.url.replace(rangeRe, `range=0-${clen - 1}`);

                // get associated data
                const data = this.linksMap.get(playlist);
                const url = this.tabId2Link.get(tabId);

                // add data link to array associated with playlist's link
                const linksArr = data.links.get(url);
                linksArr.push(details.url);
                counter++;
                // got 2 links (audio + video) this playlist's link is done
                if (linksArr.length == 2) {
                    this.tabId2Link.delete(tabId);
                    this.tabsMap.delete(tabId);
                    // chrome.tabs.remove(tabId);
                    data.waiting--;
                    // got all playlist's links, send data to server
                    if (data.waiting == 0) {
                        this.communicationHandler.sendLinks(playlist, [...data.links.entries()]);
                        this.linksMap.delete(playlist);
                    }
                }
            } catch (err) {
                console.error(`url ${details.url} is invalid`, err);
            }
        }
    }

    _isValid(url) {
        return url.includes('rbuf=0');
    }

}


const ch = new ConnectionHandler();

// socket.addEventListener('open', e => {
//     socket.send("front msg");
// });

// socket.addEventListener('message', e => {
//     console.log(`received ${e.data}`);
// })



// chrome.webRequest.onCompleted.addListener(details => {
//     // console.log(details);
//     const { tabId } = details;
//     chrome.tabs.get(tabId, tab => {
//         console.log(`${tab.url} queried ${details.url}`);
//     });
// }, {
//     urls: ["*://*.googlevideo.com/*"]
// });

// setTimeout(() => {
//     console.log("creating");
//     const url = "https://www.youtube.com/watch?v=g6cVVgr5eyc";
//     chrome.tabs.create({
//         active: false,
//         url: url
//     }, tab => {
//         console.log("created tab at " + tab.url);
//     });
// }, 2000);

