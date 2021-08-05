console.log('Working');

const PORT = 5555;

const HREFS_CODE = 1; // match with content.js codes

const connTimeout = 5; // seconds
let retries = 10;
let connEstb = false;
let counter = 0;

///////////////////////////////
// ! keep it consistent with ipc_codes.py ExtCodes
const CODES = {
    TERMINATE: 0, // TODO 
    FETCH_PLAYLIST: 1,
    PLAYLIST_FAILED: 3,
    PLAYLIST_FETCHED: 4,
    PING: 5, //depracated
    LOST_CONNECTION: 6, // irrelevant here
    CONNECTION_NOT_ESTB: 7, // irrelevant here
    FETCH_LINK: 8,
    LINK_FETCHED: 9
}
///////////////////////////////

// TODO retries....
class ConnectionHandler {
    constructor(port = 5558, retries = 3000000, connTimeout = 1, pingTime = 1) {
        this.PORT = port;
        this.START_CON_TIMEOUT = connTimeout;
        this.socket = null;
        this.retries = retries; //after retries retry time is doubled
        this.connEstb = false;
        this.connTimeout = connTimeout;
        this.pingTime = pingTime;
        this.pingedBack = true;

        this.pinger = null;
        this.init();
    }

    init() {
        this.socket = new WebSocket(`ws://127.0.0.1:${this.PORT}`);
        this.playlistExtractor = new PlaylistLinkExtractor(this);
        this.LinkExtractor = new LinkExtractor(this);

        this.socket.addEventListener('error', err => this.onError(err));
        this.socket.addEventListener('open', ev => this.onConnected(ev));
        this.socket.addEventListener('message', msg => this.onMsgRcvd(msg.data));

    }

    _reset() {
        if (this.socket !== null) {
            this.socket.close();
            this.socket = null;
        }
        if (this.pinger !== null) {
            clearInterval(this.pinger);
            this.pinger = null;
            this.pingedBack = true;
        }
        this.connEstb = false;
        this.connTimeout = this.START_CON_TIMEOUT;
    }

    onMsgRcvd(msg) {
        const msg_ob = JSON.parse(msg);
        console.log("GOT MSG: ", msg_ob);
        const code = msg_ob['code'];
        const data = msg_ob['data'];

        if (code == CODES.FETCH_PLAYLIST)
            this.playlistExtractor.addPlaylist(data['url'], msg_ob);
        else if (code == CODES.FETCH_LINK)
            this.LinkExtractor.addLink(data['url'], msg_ob);
        else if (code == CODES.PING)
            this.pingedBack = true;
        else
            console.log('Rcvd unsupported msg type', msg);
    }

    onError(err) {
        if (!this.connEstb) {
            console.log(`Failed to connect, retrying...`);

            this.retries--;
            if (this.retries < 0)
                this.connTimeout *= 2;

            setTimeout(() => this.init(), this.connTimeout * 1000);
        }
        else {
            console.log(`Error after connection, aborting`);
            setTimeout(() => this.init(), this.START_CON_TIMEOUT * 1000);
        }
        this._reset();
    }

    onConnected(ev) {
        if (this.connEstb)
            console.error('ALREADY CONNECTED');
        else {
            this.connEstb = true;
            console.log('connected', ev);
            this.pinger = setInterval(() => this._ping(), this.pingTime * 1000);
        }
    }

    _ping() {
        if (this.socket.readyState === WebSocket.CLOSED ||
            this.socket.readyState === WebSocket.CLOSING) {
            console.log('LOST CONNECTION, retrying');
            this._reset();
            this.init();
        }

        // if (!this.pingedBack) {
        //     console.log('LOST CONNECTION, retrying...');
        //     this._reset();
        //     this.init();
        // }
        // else {
        //     try {
        //         this.pingedBack = false;
        //         this.socket.send(JSON.stringify({
        //             code: CODES.PING,
        //             data: ''
        //         }));
        //         console.log('sent!');
        //     } catch (err) {
        //         // ignore will be taken care of in next ping iteration
        //     }
        // }
    }

    _sendPlaylistData(playlist, code, data, echo) {
        const msg_data = {
            ...data,
            playlist: playlist,
        };

        if (echo != null)
            msg_data['echo'] = echo;

        console.log(msg_data);

        this.socket.send(JSON.stringify({
            code: code,
            data: msg_data
        }));
    }

    sendLinks(playlist, links, titles, echo) {
        const data = {
            links: links.map(([link, dataLinks], idx) => {
                return {
                    link: link,
                    title: titles[idx],
                    dataLinks: dataLinks
                };
            })
        };

        this._sendPlaylistData(playlist, CODES.PLAYLIST_FETCHED, data, echo);
        console.log("sending ", data, echo);
    }

    sendFailureMsg(playlist, code, reason) {
        this._sendPlaylistData(playlist, code, reason);
    }

    // TODO make it consistent lmao
    sendSingleLink(link, dataLinks, echo) {
        console.log('SENDING SINGLE LINK', link, dataLinks,
            echo, '\n--------------------------');
        this.socket.send(JSON.stringify({
            code: CODES.LINK_FETCHED,
            data: {
                link: link,
                dataLinks: dataLinks,
                echo: echo
            }
        }));
    }
}


// TODO refactor this class so it uses LinkExtractor
class PlaylistLinkExtractor {
    constructor(communicationHandler) {
        this.MAX_BATCH_TABS = 5; // if playlist has > 5 links, they will be opened in separete runs

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
                    this.communicationHandler.sendFailureMsg(req.playlist, CODES.PLAYLIST_FAILED, req.reason);
            }
        });
    }

    addPlaylist(playlist, echo) {
        if (this.linksMap.has(playlist)) {
            console.log(`playlist ${playlist} already queued`);
            return;
        }

        this.linksMap.set(playlist, {
            // those that are/were procecessed
            // url -> {
            // linksArr: [string] // ready media links,
            // requiredTypes: Set<string> // at init (audio, video), deleted once found}
            links: new Map(),

            allLinks: [],
            echo: echo, // original request data
            done: 0, // how many are done
            waiting: 0, //how many are currently processed
            reqLinks: 2 // how many data links are required for each video
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
                data.links.set(url, {
                    linksArr: [],
                    requiredTypes: new Set(['audio', 'video'])
                });
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
        const links = [...playlistData.links.entries()].map(([link, { linksArr, _ }]) => [link, linksArr]);
        const titles = links.map(([link, _]) => this.link2title.get(link));


        this.communicationHandler.sendLinks(playlist, links, titles, playlistData.echo);
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
            const { links: lmap, reqLinks } = this.linksMap.get(playlist);
            const link = this.tabId2Link.get(tabId);
            const { requiredTypes } = lmap.get(link);
            // an leftover probably
            if (lmap == null || requiredTypes.length == reqLinks)
                return;

            try {
                // // swap params so single download will suffice
                // const clenRe = /clen=(\d+)/;
                // const clen = parseInt(details.url.match(clenRe)[1]);
                // const rangeRe = /range=0-\d+?/;
                // details.url = details.url.replace(rangeRe, `range=0-${clen - 1}`);

                // get associated data
                const data = this.linksMap.get(playlist);
                const url = this.tabId2Link.get(tabId);

                // add data link to array associated with playlist's link
                const { linksArr, requiredTypes } = data.links.get(url);
                const mimesRe = /mime=(\w+)/;
                const type = details.url.match(mimesRe)[1];
                if (requiredTypes.has(type))
                    requiredTypes.delete(type);
                else
                    return;

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


class LinkExtractor {
    // Handles extraction of single link
    constructor(communicationHandler) {
        this.communicationHandler = communicationHandler;

        this.linkMap = new Map(); // url -> {linksArr: [str], requiredTypes: Set[str], echo: original request}
        this.tabsMap = new Map(); // tabId -> url

        chrome.webRequest.onCompleted.addListener(details => this._linkIntecepted(details), {
            urls: ["*://*.googlevideo.com/*"]
        });
    }

    addLink(link, echo) {
        if (this.linkMap.has(link)) {
            console.log(`link ${link} already enqueued`);
            return;
        }
        this.linkMap.set(link, {
            linksArr: [],
            requiredTypes: new Set(['audio', 'video']),
            echo: echo
        });
        this._getDataLinks(link);
    }

    _getDataLinks(link) {
        chrome.tabs.create({
            active: false,
            url: link
        }, tab => {
            this.tabsMap.set(tab.id, link);
        });
    }

    _linkIntecepted(details) {
        const { tabId } = details;
        const link = this.tabsMap.get(tabId);

        if (link && this._isValid(details.url)) {
            const { linksArr, requiredTypes } = this.linkMap.get(link);
            try {
                const mimesRe = /mime=(\w+)/;
                const type = details.url.match(mimesRe)[1];

                if (requiredTypes.has(type))
                    requiredTypes.delete(type);
                else
                    return;

                linksArr.push(details.url);
                // got 2 links (audio + video) this playlist's link is done
                if (linksArr.length == 2)
                    this._tabReady(tabId, link);
            }
            catch (err) {
                console.error(`url ${details.url} is invalid`, err);
                console.log(link);
            }
        }
    }

    _tabReady(tabId, link,) {
        this.tabsMap.delete(tabId);
        const { linksArr, echo } = this.linkMap.get(link);
        this.linkMap.delete(link);

        chrome.tabs.remove(tabId);
        this.communicationHandler.sendSingleLink(link, linksArr, echo);
    }

    _isValid(url) {
        return url.includes('rbuf=0');
    }
}



function main() {
    const ch = new ConnectionHandler();
}


main();