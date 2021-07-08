console.log('Working');

const PORT = 5555;
const HREFS_CODE = 1;
const connTimeout = 5; // seconds
let retries = 10;
let connEstb = false;
let counter = 0;

const PLAYLIST_FAILED_CODE = 1;
const PLAYLIST_SUCCEEDED_CODE = 2;


class ConnectionHandler {
    constructor(port = 5555, retries = 10, connTimeout = 5) {
        this.PORT = port;
        this.socket = null;
        this.retries = retries; //after retries retry time is doubled
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
            const extractor = new LinkExtractor(this);
            data['playlists'].forEach(playlist => extractor.addPlaylist(playlist));
        });
    }

    onError(err) {
        if (!this.connEstb) {
            console.log(`Failed to connect, retrying...`);

            this.retries--;
            if (this.retries < 0)
                this.connTimeout *= 2;

            setTimeout(() => this.init(), this.connTimeout * 1000);
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

    _sendData(playlist, code, data) {
        this.socket.send(JSON.stringify({
            playlist: playlist,
            code: code,
            data: data
        }));
    }

    sendLinks(playlist, links, titles) {
        const data = links.map(([link, dataLinks], idx) => {
            return {
                link: link,
                title: titles[idx],
                dataLinks: dataLinks
            };
        });

        this._sendData(playlist, PLAYLIST_SUCCEEDED_CODE, data);
        console.log("sending ", data);
    }

    sendFailureMsg(playlist, code, reason) {
        this._sendData(playlist, code, reason);
    }
}


class LinkExtractor {
    constructor(communicationHandler) {
        this.MAX_BATCH_TABS = 10; // if playlist has > 10 links, they will be opened in separete runs

        this.playlists = [];
        this.communicationHandler = communicationHandler;

        this.linksMap = new Map();  // playlist(url) -> {links: Map<link_within_playlist, [DataLink]>, waiting: int}
        this.tabsMap = new Map(); // tabId -> playlist(url)
        this.tabId2Link = new Map(); // tabId -> link (within playlist)
        this.link2title = new Map(); // link -> video title

        // process playlists sequentially not to kill browser
        // this.playlists.forEach(playlist => this.getPlaylistItems(playlist));

        chrome.webRequest.onCompleted.addListener(details => this._linkIntecepted(details), {
            urls: ["*://*.googlevideo.com/*"]
        });

        chrome.runtime.onMessage.addListener((req, sender, resp) => {
            if (req && req.code === HREFS_CODE) {
                if (req.success) {
                    chrome.tabs.remove(sender.tab.id);

                    const plData = this.linksMap.get(req.playlist);
                    plData.allLinks = req.content.hrefs;
                    req.content.titles.forEach((title, idx) => {
                        this.link2title.set(plData.allLinks[idx], title);
                    });

                    this._openPlaylistTabs(req.playlist, plData.allLinks.slice(0, this.MAX_BATCH_TABS));
                }
                else
                    this.communicationHandler.sendFailureMsg(req.playlist, PLAYLIST_FAILED_CODE, req.reason);
            }
        });
    }

    addPlaylist(playlist) {
        if (this.linksMap.has(playlist)) {
            console.log(`playlist ${playlist} already queued`);
            return;
        }

        this.linksMap.set(playlist, {
            links: new Map(), // those that are/were procecessed
            allLinks: [],
            done: 0, // how many are done
            waiting: 0, //how many are currently processed
        });

        this.playlists.push(playlist);
        // if nothing is queued process this
        if (this.playlists.length === 1)
            this.getPlaylistItems(playlist);
    }

    getPlaylistItems(playlist) {
        console.log(`PROCESSING PLAYLIST AT ${playlist}\n
        ------------------------------------------------------`);

        chrome.tabs.create({
            active: false,
            url: playlist
        }, tab => {
            chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
                if (tabId === tab.id && info.status === 'complete') {
                    chrome.tabs.onUpdated.removeListener(listener);
                    chrome.tabs.sendMessage(tab.id, { playlist: playlist, code: HREFS_CODE });
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

    _openPlaylistTabs(playlistUrl, urls) {
        const data = this.linksMap.get(playlistUrl);

        urls.forEach(url => {
            data.waiting++;
            chrome.tabs.create({
                active: false,
                url: url
            }, tab => {
                this.tabsMap.set(tab.id, playlistUrl);
                this.tabId2Link.set(tab.id, url);
                data.links.set(url, []);
            });
        });
    }

    _tabReady(tabId, playlist, playlistData) {
        this.tabId2Link.delete(tabId);
        this.tabsMap.delete(tabId);
        chrome.tabs.remove(tabId);
        playlistData.waiting--;
        playlistData.done++;
        const processed = playlistData.waiting + playlistData.done;

        // got all playlist's links, send data to server
        if (playlistData.done == playlistData.allLinks.length) {
            this._playlistReady(playlist, playlistData);
        }
        else if (processed < playlistData.allLinks.length) {
            this._openPlaylistTabs(playlist, [playlistData.allLinks[processed]]);
        }
    }

    _playlistReady(playlist, playlistData) {
        const links = [...playlistData.links.entries()];
        const titles = links.map(([link, _]) => this.link2title.get(link));

        this.communicationHandler.sendLinks(playlist, links, titles);
        this.linksMap.delete(playlist);

        // pop queue
        this.playlists.shift();

        // run next if exists
        if (this.playlists.length > 0)
            this.getPlaylistItems(this.playlists[0]);
    }

    _linkIntecepted(details) {
        const { tabId } = details;
        const playlist = this.tabsMap.get(tabId);

        // valid single link intercepted
        if (playlist && this._isValid(details.url)) {
            const lmap = this.linksMap.get(playlist).links;
            const link = this.tabId2Link.get(tabId);
            // an leftover probably?
            if (lmap == null || lmap.get(link).length == 2)
                return;

            try {
                // swap params so single download will suffice
                const clenRe = /clen=(\d+)/;
                const clen = parseInt(details.url.match(clenRe)[1]);
                const rangeRe = /range=0-\d+?/;
                details.url = details.url.replace(rangeRe, `range=0-${clen - 1}`);

                // get associated data
                const data = this.linksMap.get(playlist);
                const url = this.tabId2Link.get(tabId);

                // add data link to array associated with playlist's link
                const linksArr = data.links.get(url);
                linksArr.push(details.url);
                counter++;
                // got 2 links (audio + video) this playlist's link is done
                if (linksArr.length == 2)
                    this._tabReady(tabId, playlist, data);

            } catch (err) {
                console.error(`url ${details.url} is invalid`, err);
                console.log(link);
                // TODO for now mark it as ready so entire playlist wont fail if one tab fails
                const data = this.linksMap.get(playlist);
                this._tabReady(tabId, playlist, data);
            }
        }
    }

    _isValid(url) {
        return url.includes('rbuf=0');
    }

}



function main() {
    const ch = new ConnectionHandler();
}


main();