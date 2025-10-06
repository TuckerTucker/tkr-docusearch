"use strict";

var XHR = XMLHttpRequest,
	img_re = /\.(a?png|avif|bmp|gif|heif|jpe?g|jfif|svg|webp|webm|mkv|mp4|m4v|mov)(\?|$)/i;

// please add translations in alphabetic order, but keep "eng" and "nor" first
// (lines ending with //m are machine translations)
var Ls = {
	"eng": {
		"tt": "English",

		"cols": {
			"c": "action buttons",
			"dur": "duration",
			"q": "quality / bitrate",
			"Ac": "audio codec",
			"Vc": "video codec",
			"Fmt": "format / container",
			"Ahash": "audio checksum",
			"Vhash": "video checksum",
			"Res": "resolution",
			"T": "filetype",
			"aq": "audio quality / bitrate",
			"vq": "video quality / bitrate",
			"pixfmt": "subsampling / pixel structure",
			"resw": "horizontal resolution",
			"resh": "vertical resolution",
			"chs": "audio channels",
			"hz": "sample rate"
		},

		"hks": [
			[
				"misc",
				["ESC", "close various things"],

				"file-manager",
				["G", "toggle list / grid view"],
				["T", "toggle thumbnails / icons"],
				["⇧ A/D", "thumbnail size"],
				["ctrl-K", "delete selected"],
				["ctrl-X", "cut selection to clipboard"],
				["ctrl-C", "copy selection to clipboard"],
				["ctrl-V", "paste (move/copy) here"],
				["Y", "download selected"],
				["F2", "rename selected"],

				"file-list-sel",
				["space", "toggle file selection"],
				["↑/↓", "move selection cursor"],
				["ctrl ↑/↓", "move cursor and viewport"],
				["⇧ ↑/↓", "select prev/next file"],
				["ctrl-A", "select all files / folders"],
			], [
				"navigation",
				["B", "toggle breadcrumbs / navpane"],
				["I/K", "prev/next folder"],
				["M", "parent folder (or unexpand current)"],
				["V", "toggle folders / textfiles in navpane"],
				["A/D", "navpane size"],
			], [
				"audio-player",
				["J/L", "prev/next song"],
				["U/O", "skip 10sec back/fwd"],
				["0..9", "jump to 0%..90%"],
				["P", "play/pause (also initiates)"],
				["S", "select playing song"],
				["Y", "download song"],
			], [
				"image-viewer",
				["J/L, ←/→", "prev/next pic"],
				["Home/End", "first/last pic"],
				["F", "fullscreen"],
				["R", "rotate clockwise"],
				["⇧ R", "rotate ccw"],
				["S", "select pic"],
				["Y", "download pic"],
			], [
				"video-player",
				["U/O", "skip 10sec back/fwd"],
				["P/K/Space", "play/pause"],
				["C", "continue playing next"],
				["V", "loop"],
				["M", "mute"],
				["[ and ]", "set loop interval"],
			], [
				"textfile-viewer",
				["I/K", "prev/next file"],
				["M", "close textfile"],
				["E", "edit textfile"],
				["S", "select file (for cut/copy/rename)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Cancel",

		"enable": "Enable",
		"danger": "DANGER",
		"clipped": "copied to clipboard",

		"ht_s1": "second",
		"ht_s2": "seconds",
		"ht_m1": "minute",
		"ht_m2": "minutes",
		"ht_h1": "hour",
		"ht_h2": "hours",
		"ht_d1": "day",
		"ht_d2": "days",
		"ht_and": " and ",

		"goh": "control-panel",
		"gop": 'previous sibling">prev',
		"gou": 'parent folder">up',
		"gon": 'next folder">next',
		"logout": "Logout ",
		"login": "Login",
		"access": " access",
		"ot_close": "close submenu",
		"ot_search": "search for files by attributes, path / name, music tags, or any combination of those$N$N&lt;code&gt;foo bar&lt;/code&gt; = must contain both «foo» and «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = must contain «foo» but not «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = start with «yana» and be an «opus» file$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = contain exactly «try unite»$N$Nthe date format is iso-8601, like$N&lt;code&gt;2009-12-31&lt;/code&gt; or &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: delete your recent uploads, or abort unfinished ones",
		"ot_bup": "bup: basic uploader, even supports netscape 4.0",
		"ot_mkdir": "mkdir: create a new directory",
		"ot_md": "new-md: create a new markdown document",
		"ot_msg": "msg: send a message to the server log",
		"ot_mp": "media player options",
		"ot_cfg": "configuration options",
		"ot_u2i": 'up2k: upload files (if you have write-access) or toggle into the search-mode to see if they exist somewhere on the server$N$Nuploads are resumable, multithreaded, and file timestamps are preserved, but it uses more CPU than [🎈]&nbsp; (the basic uploader)<br /><br />during uploads, this icon becomes a progress indicator!',
		"ot_u2w": 'up2k: upload files with resume support (close your browser and drop the same files in later)$N$Nmultithreaded, and file timestamps are preserved, but it uses more CPU than [🎈]&nbsp; (the basic uploader)<br /><br />during uploads, this icon becomes a progress indicator!',
		"ot_noie": 'Please use Chrome / Firefox / Edge',

		"ab_mkdir": "make directory",
		"ab_mkdoc": "new markdown doc",
		"ab_msg": "send msg to srv log",

		"ay_path": "skip to folders",
		"ay_files": "skip to files",

		"wt_ren": "rename selected items$NHotkey: F2",
		"wt_del": "delete selected items$NHotkey: ctrl-K",
		"wt_cut": "cut selected items &lt;small&gt;(then paste somewhere else)&lt;/small&gt;$NHotkey: ctrl-X",
		"wt_cpy": "copy selected items to clipboard$N(to paste them somewhere else)$NHotkey: ctrl-C",
		"wt_pst": "paste a previously cut / copied selection$NHotkey: ctrl-V",
		"wt_selall": "select all files$NHotkey: ctrl-A (when file focused)",
		"wt_selinv": "invert selection",
		"wt_zip1": "download this folder as archive",
		"wt_selzip": "download selection as archive",
		"wt_seldl": "download selection as separate files$NHotkey: Y",
		"wt_npirc": "copy irc-formatted track info",
		"wt_nptxt": "copy plaintext track info",
		"wt_m3ua": "add to m3u playlist (click <code>📻copy</code> later)",
		"wt_m3uc": "copy m3u playlist to clipboard",
		"wt_grid": "toggle grid / list view$NHotkey: G",
		"wt_prev": "previous track$NHotkey: J",
		"wt_play": "play / pause$NHotkey: P",
		"wt_next": "next track$NHotkey: L",

		"ul_par": "parallel uploads:",
		"ut_rand": "randomize filenames",
		"ut_u2ts": "copy the last-modified timestamp$Nfrom your filesystem to the server\">📅",
		"ut_ow": "overwrite existing files on the server?$N🛡️: never (will generate a new filename instead)$N🕒: overwrite if server-file is older than yours$N♻️: always overwrite if the files are different",
		"ut_mt": "continue hashing other files while uploading$N$Nmaybe disable if your CPU or HDD is a bottleneck",
		"ut_ask": 'ask for confirmation before upload starts">💭',
		"ut_pot": "improve upload speed on slow devices$Nby making the UI less complex",
		"ut_srch": "don't actually upload, instead check if the files already $N exist on the server (will scan all folders you can read)",
		"ut_par": "pause uploads by setting it to 0$N$Nincrease if your connection is slow / high latency$N$Nkeep it 1 on LAN or if the server HDD is a bottleneck",
		"ul_btn": "drop files / folders<br>here (or click me)",
		"ul_btnu": "U P L O A D",
		"ul_btns": "S E A R C H",

		"ul_hash": "hash",
		"ul_send": "send",
		"ul_done": "done",
		"ul_idle1": "no uploads are queued yet",
		"ut_etah": "average &lt;em&gt;hashing&lt;/em&gt; speed, and estimated time until finish",
		"ut_etau": "average &lt;em&gt;upload&lt;/em&gt; speed and estimated time until finish",
		"ut_etat": "average &lt;em&gt;total&lt;/em&gt; speed and estimated time until finish",

		"uct_ok": "completed successfully",
		"uct_ng": "no-good: failed / rejected / not-found",
		"uct_done": "ok and ng combined",
		"uct_bz": "hashing or uploading",
		"uct_q": "idle, pending",

		"utl_name": "filename",
		"utl_ulist": "list",
		"utl_ucopy": "copy",
		"utl_links": "links",
		"utl_stat": "status",
		"utl_prog": "progress",

		// keep short:
		"utl_404": "404",
		"utl_err": "ERROR",
		"utl_oserr": "OS-error",
		"utl_found": "found",
		"utl_defer": "defer",
		"utl_yolo": "YOLO",
		"utl_done": "done",

		"ul_flagblk": "the files were added to the queue</b><br>however there is a busy up2k in another browser tab,<br>so waiting for that to finish first",
		"ul_btnlk": "the server configuration has locked this switch into this state",

		"udt_up": "Upload",
		"udt_srch": "Search",
		"udt_drop": "drop it here",

		"u_nav_m": '<h6>aight, what do you have?</h6><code>Enter</code> = Files (one or more)\n<code>ESC</code> = One folder (including subfolders)',
		"u_nav_b": '<a href="#" id="modal-ok">Files</a><a href="#" id="modal-ng">One folder</a>',

		"cl_opts": "switches",
		"cl_hfsz": "filesize",
		"cl_themes": "theme",
		"cl_langs": "language",
		"cl_ziptype": "folder download",
		"cl_uopts": "up2k switches",
		"cl_favico": "favicon",
		"cl_bigdir": "big dirs",
		"cl_hsort": "#sort",
		"cl_keytype": "key notation",
		"cl_hiddenc": "hidden columns",
		"cl_hidec": "hide",
		"cl_reset": "reset",
		"cl_hpick": "tap on column headers to hide in the table below",
		"cl_hcancel": "column hiding aborted",

		"ct_grid": '田 the grid',
		"ct_ttips": '◔ ◡ ◔">ℹ️ tooltips',
		"ct_thumb": 'in grid-view, toggle icons or thumbnails$NHotkey: T">🖼️ thumbs',
		"ct_csel": 'use CTRL and SHIFT for file selection in grid-view">sel',
		"ct_ihop": 'when the image viewer is closed, scroll down to the last viewed file">g⮯',
		"ct_dots": 'show hidden files (if server permits)">dotfiles',
		"ct_qdel": 'when deleting files, only ask for confirmation once">qdel',
		"ct_dir1st": 'sort folders before files">📁 first',
		"ct_nsort": 'natural sort (for filenames with leading digits)">nsort',
		"ct_utc": 'show all datetimes in UTC">UTC',
		"ct_readme": 'show README.md in folder listings">📜 readme',
		"ct_idxh": 'show index.html instead of folder listing">htm',
		"ct_sbars": 'show scrollbars">⟊',

		"cut_umod": "if a file already exists on the server, update the server's last-modified timestamp to match your local file (requires write+delete permissions)\">re📅",

		"cut_turbo": "the yolo button, you probably DO NOT want to enable this:$N$Nuse this if you were uploading a huge amount of files and had to restart for some reason, and want to continue the upload ASAP$N$Nthis replaces the hash-check with a simple <em>&quot;does this have the same filesize on the server?&quot;</em> so if the file contents are different it will NOT be uploaded$N$Nyou should turn this off when the upload is done, and then &quot;upload&quot; the same files again to let the client verify them\">turbo",

		"cut_datechk": "has no effect unless the turbo button is enabled$N$Nreduces the yolo factor by a tiny amount; checks whether the file timestamps on the server matches yours$N$Nshould <em>theoretically</em> catch most unfinished / corrupted uploads, but is not a substitute for doing a verification pass with turbo disabled afterwards\">date-chk",

		"cut_u2sz": "size (in MiB) of each upload chunk; big values fly better across the atlantic. Try low values on very unreliable connections",

		"cut_flag": "ensure only one tab is uploading at a time $N -- other tabs must have this enabled too $N -- only affects tabs on the same domain",

		"cut_az": "upload files in alphabetical order, rather than smallest-file-first$N$Nalphabetical order can make it easier to eyeball if something went wrong on the server, but it makes uploading slightly slower on fiber / LAN",

		"cut_nag": "OS notification when upload completes$N(only if the browser or tab is not active)",
		"cut_sfx": "audible alert when upload completes$N(only if the browser or tab is not active)",

		"cut_mt": "use multithreading to accelerate file hashing$N$Nthis uses web-workers and requires$Nmore RAM (up to 512 MiB extra)$N$Nmakes https 30% faster, http 4.5x faster\">mt",

		"cut_wasm": "use wasm instead of the browser's built-in hasher; improves speed on chrome-based browsers but increases CPU load, and many older versions of chrome have bugs which makes the browser consume all RAM and crash if this is enabled\">wasm",

		"cft_text": "favicon text (blank and refresh to disable)",
		"cft_fg": "foreground color",
		"cft_bg": "background color",

		"cdt_lim": "max number of files to show in a folder",
		"cdt_ask": "when scrolling to the bottom,$Ninstead of loading more files,$Nask what to do",
		"cdt_hsort": "how many sorting rules (&lt;code&gt;,sorthref&lt;/code&gt;) to include in media-URLs. Setting this to 0 will also ignore sorting-rules included in media links when clicking them",

		"tt_entree": "show navpane (directory tree sidebar)$NHotkey: B",
		"tt_detree": "show breadcrumbs$NHotkey: B",
		"tt_visdir": "scroll to selected folder",
		"tt_ftree": "toggle folder-tree / textfiles$NHotkey: V",
		"tt_pdock": "show parent folders in a docked pane at the top",
		"tt_dynt": "autogrow as tree expands",
		"tt_wrap": "word wrap",
		"tt_hover": "reveal overflowing lines on hover$N( breaks scrolling unless mouse $N&nbsp; cursor is in the left gutter )",

		"ml_pmode": "at end of folder...",
		"ml_btns": "cmds",
		"ml_tcode": "transcode",
		"ml_tcode2": "transcode to",
		"ml_tint": "tint",
		"ml_eq": "audio equalizer",
		"ml_drc": "dynamic range compressor",

		"mt_loop": "loop/repeat one song\">🔁",
		"mt_one": "stop after one song\">1️⃣",
		"mt_shuf": "shuffle the songs in each folder\">🔀",
		"mt_aplay": "autoplay if there is a song-ID in the link you clicked to access the server$N$Ndisabling this will also stop the page URL from being updated with song-IDs when playing music, to prevent autoplay if these settings are lost but the URL remains\">a▶",
		"mt_preload": "start loading the next song near the end for gapless playback\">preload",
		"mt_prescan": "go to the next folder before the last song$Nends, keeping the webbrowser happy$Nso it doesn't stop the playback\">nav",
		"mt_fullpre": "try to preload the entire song;$N✅ enable on <b>unreliable</b> connections,$N❌ <b>disable</b> on slow connections probably\">full",
		"mt_fau": "on phones, prevent music from stopping if the next song doesn't preload fast enough (can make tags display glitchy)\">☕️",
		"mt_waves": "waveform seekbar:$Nshow audio amplitude in the scrubber\">~s",
		"mt_npclip": "show buttons for clipboarding the currently playing song\">/np",
		"mt_m3u_c": "show buttons for clipboarding the$Nselected songs as m3u8 playlist entries\">📻",
		"mt_octl": "os integration (media hotkeys / osd)\">os-ctl",
		"mt_oseek": "allow seeking through os integration$N$Nnote: on some devices (iPhones),$Nthis replaces the next-song button\">seek",
		"mt_oscv": "show album cover in osd\">art",
		"mt_follow": "keep the playing track scrolled into view\">🎯",
		"mt_compact": "compact controls\">⟎",
		"mt_uncache": "clear cache &nbsp;(try this if your browser cached$Na broken copy of a song so it refuses to play)\">uncache",
		"mt_mloop": "loop the open folder\">🔁 loop",
		"mt_mnext": "load the next folder and continue\">📂 next",
		"mt_mstop": "stop playback\">⏸ stop",
		"mt_cflac": "convert flac / wav to {0}\">flac",
		"mt_caac": "convert aac / m4a to {0}\">aac",
		"mt_coth": "convert all others (not mp3) to {0}\">oth",
		"mt_c2opus": "best choice for desktops, laptops, android\">opus",
		"mt_c2owa": "opus-weba, for iOS 17.5 and newer\">owa",
		"mt_c2caf": "opus-caf, for iOS 11 through 17\">caf",
		"mt_c2mp3": "use this on very old devices\">mp3",
		"mt_c2flac": "best sound quality, but huge downloads\">flac",
		"mt_c2wav": "uncompressed playback (even bigger)\">wav",
		"mt_c2ok": "nice, good choice",
		"mt_c2nd": "that's not the recommended output format for your device, but that's fine",
		"mt_c2ng": "your device does not seem to support this output format, but let's try anyways",
		"mt_xowa": "there are bugs in iOS preventing background playback using this format; please use caf or mp3 instead",
		"mt_tint": "background level (0-100) on the seekbar$Nto make buffering less distracting",
		"mt_eq": "enables the equalizer and gain control;$N$Nboost &lt;code&gt;0&lt;/code&gt; = standard 100% volume (unmodified)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = standard stereo (unmodified)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% left-right crossfeed$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = vocal removal :^)$N$Nenabling the equalizer makes gapless albums fully gapless, so leave it on with all the values at zero (except width = 1) if you care about that",
		"mt_drc": "enables the dynamic range compressor (volume flattener / brickwaller); will also enable EQ to balance the spaghetti, so set all EQ fields except for 'width' to 0 if you don't want it$N$Nlowers the volume of audio above THRESHOLD dB; for every RATIO dB past THRESHOLD there is 1 dB of output, so default values of tresh -24 and ratio 12 means it should never get louder than -22 dB and it is safe to increase the equalizer boost to 0.8, or even 1.8 with ATK 0 and a huge RLS like 90 (only works in firefox; RLS is max 1 in other browsers)$N$N(see wikipedia, they explain it much better)",

		"mb_play": "play",
		"mm_hashplay": "play this audio file?",
		"mm_m3u": "press <code>Enter/OK</code> to Play\npress <code>ESC/Cancel</code> to Edit",
		"mp_breq": "need firefox 82+ or chrome 73+ or iOS 15+",
		"mm_bload": "now loading...",
		"mm_bconv": "converting to {0}, please wait...",
		"mm_opusen": "your browser cannot play aac / m4a files;\ntranscoding to opus is now enabled",
		"mm_playerr": "playback failed: ",
		"mm_eabrt": "The playback attempt was cancelled",
		"mm_enet": "Your internet connection is wonky",
		"mm_edec": "This file is supposedly corrupted??",
		"mm_esupp": "Your browser does not understand this audio format",
		"mm_eunk": "Unknown Errol",
		"mm_e404": "Could not play audio; error 404: File not found.",
		"mm_e403": "Could not play audio; error 403: Access denied.\n\nTry pressing F5 to reload, maybe you got logged out",
		"mm_e500": "Could not play audio; error 500: Check server logs.",
		"mm_e5xx": "Could not play audio; server error ",
		"mm_nof": "not finding any more audio files nearby",
		"mm_prescan": "Looking for music to play next...",
		"mm_scank": "Found the next song:",
		"mm_uncache": "cache cleared; all songs will redownload on next playback",
		"mm_hnf": "that song no longer exists",

		"im_hnf": "that image no longer exists",

		"f_empty": 'this folder is empty',
		"f_chide": 'this will hide the column «{0}»\n\nyou can unhide columns in the settings tab',
		"f_bigtxt": "this file is {0} MiB large -- really view as text?",
		"f_bigtxt2": "view just the end of the file instead? this will also enable following/tailing, showing newly added lines of text in real time",
		"fbd_more": '<div id="blazy">showing <code>{0}</code> of <code>{1}</code> files; <a href="#" id="bd_more">show {2}</a> or <a href="#" id="bd_all">show all</a></div>',
		"fbd_all": '<div id="blazy">showing <code>{0}</code> of <code>{1}</code> files; <a href="#" id="bd_all">show all</a></div>',
		"f_anota": "only {0} of the {1} items were selected;\nto select the full folder, first scroll to the bottom",

		"f_dls": 'the file links in the current folder have\nbeen changed into download links',

		"f_partial": "To safely download a file which is currently being uploaded, please click the file which has the same filename, but without the <code>.PARTIAL</code> file extension. Please press CANCEL or Escape to do this.\n\nPressing OK / Enter will ignore this warning and continue downloading the <code>.PARTIAL</code> scratchfile instead, which will almost definitely give you corrupted data.",

		"ft_paste": "paste {0} items$NHotkey: ctrl-V",
		"fr_eperm": 'cannot rename:\nyou do not have “move” permission in this folder',
		"fd_eperm": 'cannot delete:\nyou do not have “delete” permission in this folder',
		"fc_eperm": 'cannot cut:\nyou do not have “move” permission in this folder',
		"fp_eperm": 'cannot paste:\nyou do not have “write” permission in this folder',
		"fr_emore": "select at least one item to rename",
		"fd_emore": "select at least one item to delete",
		"fc_emore": "select at least one item to cut",
		"fcp_emore": "select at least one item to copy to clipboard",

		"fs_sc": "share the folder you're in",
		"fs_ss": "share the selected files",
		"fs_just1d": "you cannot select more than one folder,\nor mix files and folders in one selection",
		"fs_abrt": "❌ abort",
		"fs_rand": "🎲 rand.name",
		"fs_go": "✅ create share",
		"fs_name": "name",
		"fs_src": "source",
		"fs_pwd": "passwd",
		"fs_exp": "expiry",
		"fs_tmin": "min",
		"fs_thrs": "hours",
		"fs_tdays": "days",
		"fs_never": "eternal",
		"fs_pname": "optional link name; will be random if blank",
		"fs_tsrc": "the file or folder to share",
		"fs_ppwd": "optional password",
		"fs_w8": "creating share...",
		"fs_ok": "press <code>Enter/OK</code> to Clipboard\npress <code>ESC/Cancel</code> to Close",

		"frt_dec": "may fix some cases of broken filenames\">url-decode",
		"frt_rst": "reset modified filenames back to the original ones\">↺ reset",
		"frt_abrt": "abort and close this window\">❌ cancel",
		"frb_apply": "APPLY RENAME",
		"fr_adv": "batch / metadata / pattern renaming\">advanced",
		"fr_case": "case-sensitive regex\">case",
		"fr_win": "windows-safe names; replace <code>&lt;&gt;:&quot;\\|?*</code> with japanese fullwidth characters\">win",
		"fr_slash": "replace <code>/</code> with a character that doesn't cause new folders to be created\">no /",
		"fr_re": "regex search pattern to apply to original filenames; capturing groups can be referenced in the format field below like &lt;code&gt;(1)&lt;/code&gt; and &lt;code&gt;(2)&lt;/code&gt; and so on",
		"fr_fmt": "inspired by foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; is replaced by song title,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; skips [this] part if artist is blank$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; pads tracknumber to 2 digits",
		"fr_pdel": "delete",
		"fr_pnew": "save as",
		"fr_pname": "provide a name for your new preset",
		"fr_aborted": "aborted",
		"fr_lold": "old name",
		"fr_lnew": "new name",
		"fr_tags": "tags for the selected files (read-only, just for reference):",
		"fr_busy": "renaming {0} items...\n\n{1}",
		"fr_efail": "rename failed:\n",
		"fr_nchg": "{0} of the new names were altered due to <code>win</code> and/or <code>no /</code>\n\nOK to continue with these altered new names?",

		"fd_ok": "delete OK",
		"fd_err": "delete failed:\n",
		"fd_none": "nothing was deleted; maybe blocked by server config (xbd)?",
		"fd_busy": "deleting {0} items...\n\n{1}",
		"fd_warn1": "DELETE these {0} items?",
		"fd_warn2": "<b>Last chance!</b> No way to undo. Delete?",

		"fc_ok": "cut {0} items",
		"fc_warn": 'cut {0} items\n\nbut: only <b>this</b> browser-tab can paste them\n(since the selection is so absolutely massive)',

		"fcc_ok": "copied {0} items to clipboard",
		"fcc_warn": 'copied {0} items to clipboard\n\nbut: only <b>this</b> browser-tab can paste them\n(since the selection is so absolutely massive)',

		"fp_apply": "use these names",
		"fp_ecut": "first cut or copy some files / folders to paste / move\n\nnote: you can cut / paste across different browser tabs",
		"fp_ename": "{0} items cannot be moved here because the names are already taken. Give them new names below to continue, or blank the name to skip them:",
		"fcp_ename": "{0} items cannot be copied here because the names are already taken. Give them new names below to continue, or blank the name to skip them:",
		"fp_emore": "there are still some filename collisions left to fix",
		"fp_ok": "move OK",
		"fcp_ok": "copy OK",
		"fp_busy": "moving {0} items...\n\n{1}",
		"fcp_busy": "copying {0} items...\n\n{1}",
		"fp_abrt": "aborting...",
		"fp_err": "move failed:\n",
		"fcp_err": "copy failed:\n",
		"fp_confirm": "move these {0} items here?",
		"fcp_confirm": "copy these {0} items here?",
		"fp_etab": 'failed to read clipboard from other browser tab',
		"fp_name": "uploading a file from your device. Give it a name:",
		"fp_both_m": '<h6>choose what to paste</h6><code>Enter</code> = Move {0} files from «{1}»\n<code>ESC</code> = Upload {2} files from your device',
		"fcp_both_m": '<h6>choose what to paste</h6><code>Enter</code> = Copy {0} files from «{1}»\n<code>ESC</code> = Upload {2} files from your device',
		"fp_both_b": '<a href="#" id="modal-ok">Move</a><a href="#" id="modal-ng">Upload</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Copy</a><a href="#" id="modal-ng">Upload</a>',

		"mk_noname": "type a name into the text field on the left before you do that :p",

		"tv_load": "Loading text document:\n\n{0}\n\n{1}% ({2} of {3} MiB loaded)",
		"tv_xe1": "could not load textfile:\n\nerror ",
		"tv_xe2": "404, file not found",
		"tv_lst": "list of textfiles in",
		"tvt_close": "return to folder view$NHotkey: M (or Esc)\">❌ close",
		"tvt_dl": "download this file$NHotkey: Y\">💾 download",
		"tvt_prev": "show previous document$NHotkey: i\">⬆ prev",
		"tvt_next": "show next document$NHotkey: K\">⬇ next",
		"tvt_sel": "select file &nbsp; ( for cut / copy / delete / ... )$NHotkey: S\">sel",
		"tvt_edit": "open file in text editor$NHotkey: E\">✏️ edit",
		"tvt_tail": "monitor file for changes; show new lines in real time\">📡 follow",
		"tvt_wrap": "word-wrap\">↵",
		"tvt_atail": "lock scroll to bottom of page\">⚓",
		"tvt_ctail": "decode terminal colors (ansi escape codes)\">🌈",
		"tvt_ntail": "scrollback limit (how many bytes of text to keep loaded)",

		"m3u_add1": "song added to m3u playlist",
		"m3u_addn": "{0} songs added to m3u playlist",
		"m3u_clip": "m3u playlist now copied to clipboard\n\nyou should create a new textfile named something.m3u and paste the playlist in that document; this will make it playable",

		"gt_vau": "don't show videos, just play the audio\">🎧",
		"gt_msel": "enable file selection; ctrl-click a file to override$N$N&lt;em&gt;when active: doubleclick a file / folder to open it&lt;/em&gt;$N$NHotkey: S\">multiselect",
		"gt_crop": "center-crop thumbnails\">crop",
		"gt_3x": "hi-res thumbnails\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "chop",
		"gt_sort": "sort by",
		"gt_name": "name",
		"gt_sz": "size",
		"gt_ts": "date",
		"gt_ext": "type",
		"gt_c1": "truncate filenames more (show less)",
		"gt_c2": "truncate filenames less (show more)",

		"sm_w8": "searching...",
		"sm_prev": "search results below are from a previous query:\n  ",
		"sl_close": "close search results",
		"sl_hits": "showing {0} hits",
		"sl_moar": "load more",

		"s_sz": "size",
		"s_dt": "date",
		"s_rd": "path",
		"s_fn": "name",
		"s_ta": "tags",
		"s_ua": "up@",
		"s_ad": "adv.",
		"s_s1": "minimum MiB",
		"s_s2": "maximum MiB",
		"s_d1": "min. iso8601",
		"s_d2": "max. iso8601",
		"s_u1": "uploaded after",
		"s_u2": "and/or before",
		"s_r1": "path contains &nbsp; (space-separated)",
		"s_f1": "name contains &nbsp; (negate with -nope)",
		"s_t1": "tags contains &nbsp; (^=start, end=$)",
		"s_a1": "specific metadata properties",

		"md_eshow": "cannot render ",
		"md_off": "[📜<em>readme</em>] disabled in [⚙️] -- document hidden",

		"badreply": "Failed to parse reply from server",

		"xhr403": "403: Access denied\n\ntry pressing F5, maybe you got logged out",
		"xhr0": "unknown (probably lost connection to server, or server is offline)",
		"cf_ok": "sorry about that -- DD" + wah + "oS protection kicked in\n\nthings should resume in about 30 sec\n\nif nothing happens, hit F5 to reload the page",
		"tl_xe1": "could not list subfolders:\n\nerror ",
		"tl_xe2": "404: Folder not found",
		"fl_xe1": "could not list files in folder:\n\nerror ",
		"fl_xe2": "404: Folder not found",
		"fd_xe1": "could not create subfolder:\n\nerror ",
		"fd_xe2": "404: Parent folder not found",
		"fsm_xe1": "could not send message:\n\nerror ",
		"fsm_xe2": "404: Parent folder not found",
		"fu_xe1": "failed to load unpost list from server:\n\nerror ",
		"fu_xe2": "404: File not found??",

		"fz_tar": "uncompressed gnu-tar file (linux / mac)",
		"fz_pax": "uncompressed pax-format tar (slower)",
		"fz_targz": "gnu-tar with gzip level 3 compression$N$Nthis is usually very slow, so$Nuse uncompressed tar instead",
		"fz_tarxz": "gnu-tar with xz level 1 compression$N$Nthis is usually very slow, so$Nuse uncompressed tar instead",
		"fz_zip8": "zip with utf8 filenames (maybe wonky on windows 7 and older)",
		"fz_zipd": "zip with traditional cp437 filenames, for really old software",
		"fz_zipc": "cp437 with crc32 computed early,$Nfor MS-DOS PKZIP v2.04g (october 1993)$N(takes longer to process before download can start)",

		"un_m1": "you can delete your recent uploads (or abort unfinished ones) below",
		"un_upd": "refresh",
		"un_m4": "or share the files visible below:",
		"un_ulist": "show",
		"un_ucopy": "copy",
		"un_flt": "optional filter:&nbsp; URL must contain",
		"un_fclr": "clear filter",
		"un_derr": 'unpost-delete failed:\n',
		"un_f5": 'something broke, please try a refresh or hit F5',
		"un_uf5": "sorry but you have to refresh the page (for example by pressing F5 or CTRL-R) before this upload can be aborted",
		"un_nou": '<b>warning:</b> server too busy to show unfinished uploads; click the "refresh" link in a bit',
		"un_noc": '<b>warning:</b> unpost of fully uploaded files is not enabled/permitted in server config',
		"un_max": "showing first 2000 files (use the filter)",
		"un_avail": "{0} recent uploads can be deleted<br />{1} unfinished ones can be aborted",
		"un_m2": "sorted by upload time; most recent first:",
		"un_no1": "sike! no uploads are sufficiently recent",
		"un_no2": "sike! no uploads matching that filter are sufficiently recent",
		"un_next": "delete the next {0} files below",
		"un_abrt": "abort",
		"un_del": "delete",
		"un_m3": "loading your recent uploads...",
		"un_busy": "deleting {0} files...",
		"un_clip": "{0} links copied to clipboard",

		"u_https1": "you should",
		"u_https2": "switch to https",
		"u_https3": "for better performance",
		"u_ancient": 'your browser is impressively ancient -- maybe you should <a href="#" onclick="goto(\'bup\')">use bup instead</a>',
		"u_nowork": "need firefox 53+ or chrome 57+ or iOS 11+",
		"tail_2old": "need firefox 105+ or chrome 71+ or iOS 14.5+",
		"u_nodrop": 'your browser is too old for drag-and-drop uploading',
		"u_notdir": "that's not a folder!\n\nyour browser is too old,\nplease try dragdrop instead",
		"u_uri": "to dragdrop images from other browser windows,\nplease drop it onto the big upload button",
		"u_enpot": 'switch to <a href="#">potato UI</a> (may improve upload speed)',
		"u_depot": 'switch to <a href="#">fancy UI</a> (may reduce upload speed)',
		"u_gotpot": 'switching to the potato UI for improved upload speed,\n\nfeel free to disagree and switch back!',
		"u_pott": "<p>files: &nbsp; <b>{0}</b> finished, &nbsp; <b>{1}</b> failed, &nbsp; <b>{2}</b> busy, &nbsp; <b>{3}</b> queued</p>",
		"u_ever": "this is the basic uploader; up2k needs at least<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'this is the basic uploader; <a href="#" id="u2yea">up2k</a> is better',
		"u_uput": 'optimize for speed (skip checksum)',
		"u_ewrite": 'you do not have write-access to this folder',
		"u_eread": 'you do not have read-access to this folder',
		"u_enoi": 'file-search is not enabled in server config',
		"u_enoow": "overwrite will not work here; need Delete-permission",
		"u_badf": 'These {0} files (of {1} total) were skipped, possibly due to filesystem permissions:\n\n',
		"u_blankf": 'These {0} files (of {1} total) are blank / empty; upload them anyways?\n\n',
		"u_applef": 'These {0} files (of {1} total) are probably undesirable;\nPress <code>OK/Enter</code> to SKIP the following files,\nPress <code>Cancel/ESC</code> to NOT exclude, and UPLOAD those as well:\n\n',
		"u_just1": '\nMaybe it works better if you select just one file',
		"u_ff_many": "if you're using <b>Linux / MacOS / Android,</b> then this amount of files <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>may</em> crash Firefox!</a>\nif that happens, please try again (or use Chrome).",
		"u_up_life": "This upload will be deleted from the server\n{0} after it completes",
		"u_asku": 'upload these {0} files to <code>{1}</code>',
		"u_unpt": "you can undo / delete this upload using the top-left 🧯",
		"u_bigtab": 'about to show {0} files\n\nthis may crash your browser, are you sure?',
		"u_scan": 'Scanning files...',
		"u_dirstuck": 'directory iterator got stuck trying to access the following {0} items; will skip:',
		"u_etadone": 'Done ({0}, {1} files)',
		"u_etaprep": '(preparing to upload)',
		"u_hashdone": 'hashing done',
		"u_hashing": 'hash',
		"u_hs": 'handshaking...',
		"u_started": "the files are now being uploaded; see [🚀]",
		"u_dupdefer": "duplicate; will be processed after all other files",
		"u_actx": "click this text to prevent loss of<br />performance when switching to other windows/tabs",
		"u_fixed": "OK!&nbsp; Fixed it 👍",
		"u_cuerr": "failed to upload chunk {0} of {1};\nprobably harmless, continuing\n\nfile: {2}",
		"u_cuerr2": "server rejected upload (chunk {0} of {1});\nwill retry later\n\nfile: {2}\n\nerror ",
		"u_ehstmp": "will retry; see bottom-right",
		"u_ehsfin": "server rejected the request to finalize upload; retrying...",
		"u_ehssrch": "server rejected the request to perform search; retrying...",
		"u_ehsinit": "server rejected the request to initiate upload; retrying...",
		"u_eneths": "network error while performing upload handshake; retrying...",
		"u_enethd": "network error while testing target existence; retrying...",
		"u_cbusy": "waiting for server to trust us again after a network glitch...",
		"u_ehsdf": "server ran out of disk space!\n\nwill keep retrying, in case someone\nfrees up enough space to continue",
		"u_emtleak1": "it looks like your webbrowser may have a memory leak;\nplease",
		"u_emtleak2": ' <a href="{0}">switch to https (recommended)</a> or ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'try the following:\n<ul><li>hit <code>F5</code> to refresh the page</li><li>then disable the &nbsp;<code>mt</code>&nbsp; button in the &nbsp;<code>⚙️ settings</code></li><li>and try that upload again</li></ul>Uploads will be a bit slower, but oh well.\nSorry for the trouble !\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">has a bugfix</a> for this',
		"u_emtleakf": 'try the following:\n<ul><li>hit <code>F5</code> to refresh the page</li><li>then enable <code>🥔</code> (potato) in the upload UI<li>and try that upload again</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">will hopefully have a bugfix</a> at some point',
		"u_s404": "not found on server",
		"u_expl": "explain",
		"u_maxconn": "most browsers limit this to 6, but firefox lets you raise it with <code>connections-per-server</code> in <code>about:config</code>",
		"u_tu": '<p class="warn">WARNING: turbo enabled, <span>&nbsp;client may not detect and resume incomplete uploads; see turbo-button tooltip</span></p>',
		"u_ts": '<p class="warn">WARNING: turbo enabled, <span>&nbsp;search results can be incorrect; see turbo-button tooltip</span></p>',
		"u_turbo_c": "turbo is disabled in server config",
		"u_turbo_g": "disabling turbo because you don't have\ndirectory listing privileges within this volume",
		"u_life_cfg": 'autodelete after <input id="lifem" p="60" /> min (or <input id="lifeh" p="3600" /> hours)',
		"u_life_est": 'upload will be deleted <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'this folder enforces a\nmax lifetime of {0}',
		"u_unp_ok": 'unpost is allowed for {0}',
		"u_unp_ng": 'unpost will NOT be allowed',
		"ue_ro": 'your access to this folder is Read-Only\n\n',
		"ue_nl": 'you are currently not logged in',
		"ue_la": 'you are currently logged in as "{0}"',
		"ue_sr": 'you are currently in file-search mode\n\nswitch to upload-mode by clicking the magnifying glass 🔎 (next to the big SEARCH button), and try uploading again\n\nsorry',
		"ue_ta": 'try uploading again, it should work now',
		"ue_ab": "this file is already being uploaded into another folder, and that upload must be completed before the file can be uploaded elsewhere.\n\nYou can abort and forget the initial upload using the top-left 🧯",
		"ur_1uo": "OK: File uploaded successfully",
		"ur_auo": "OK: All {0} files uploaded successfully",
		"ur_1so": "OK: File found on server",
		"ur_aso": "OK: All {0} files found on server",
		"ur_1un": "Upload failed, sorry",
		"ur_aun": "All {0} uploads failed, sorry",
		"ur_1sn": "File was NOT found on server",
		"ur_asn": "The {0} files were NOT found on server",
		"ur_um": "Finished;\n{0} uploads OK,\n{1} uploads failed, sorry",
		"ur_sm": "Finished;\n{0} files found on server,\n{1} files NOT found on server",

		"lang_set": "refresh to make the change take effect?",
	},
	"nor": {
		"tt": "Norsk",

		"cols": {
			"c": "handlingsknapper",
			"dur": "varighet",
			"q": "kvalitet / bitrate",
			"Ac": "lyd-format",
			"Vc": "video-format",
			"Fmt": "format / innpakning",
			"Ahash": "lyd-kontrollsum",
			"Vhash": "video-kontrollsum",
			"Res": "oppløsning",
			"T": "filtype",
			"aq": "lydkvalitet / bitrate",
			"vq": "videokvalitet / bitrate",
			"pixfmt": "fargekoding / detaljenivå",
			"resw": "horisontal oppløsning",
			"resh": "vertikal oppløsning",
			"chs": "lydkanaler",
			"hz": "lyd-oppløsning"
		},

		"hks": [
			[
				"ymse",
				["ESC", "lukk saker og ting"],

				"filbehandler",
				["G", "listevisning eller ikoner"],
				["T", "miniatyrbilder på/av"],
				["⇧ A/D", "ikonstørrelse"],
				["ctrl-K", "slett valgte"],
				["ctrl-X", "klipp ut valgte"],
				["ctrl-C", "kopiér til utklippstavle"],
				["ctrl-V", "lim inn (flytt/kopiér)"],
				["Y", "last ned valgte"],
				["F2", "endre navn på valgte"],

				"filmarkering",
				["space", "marker fil"],
				["↑/↓", "flytt markør"],
				["ctrl ↑/↓", "flytt markør og scroll"],
				["⇧ ↑/↓", "velg forr./neste fil"],
				["ctrl-A", "velg alle filer / mapper"],
			], [
				"navigering",
				["B", "mappehierarki eller filsti"],
				["I/K", "forr./neste mappe"],
				["M", "ett nivå opp (eller lukk)"],
				["V", "vis mapper eller tekstfiler"],
				["A/D", "panelstørrelse"],
			], [
				"musikkspiller",
				["J/L", "forr./neste sang"],
				["U/O", "hopp 10sek bak/frem"],
				["0..9", "hopp til 0%..90%"],
				["P", "pause, eller start / fortsett"],
				["S", "marker spillende sang"],
				["Y", "last ned sang"],
			], [
				"bildeviser",
				["J/L, ←/→", "forr./neste bilde"],
				["Home/End", "første/siste bilde"],
				["F", "fullskjermvisning"],
				["R", "rotere mot høyre"],
				["⇧ R", "rotere mot venstre"],
				["S", "marker bilde"],
				["Y", "last ned bilde"],
			], [
				"videospiller",
				["U/O", "hopp 10sek bak/frem"],
				["P/K/Space", "pause / fortsett"],
				["C", "fortsett til neste fil"],
				["V", "gjenta avspilling"],
				["M", "lyd av/på"],
				["[ og ]", "gjentaksintervall"],
			], [
				"dokumentviser",
				["I/K", "forr./neste fil"],
				["M", "lukk tekstdokument"],
				["E", "rediger tekstdokument"],
				["S", "marker fil (for F2/ctrl-x/...)"],
				["Y", "last ned tekstfil"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Avbryt",

		"enable": "Aktiv",
		"danger": "VARSKU",
		"clipped": "kopiert til utklippstavlen",

		"ht_s1": "sekund",
		"ht_s2": "sekunder",
		"ht_m1": "minutt",
		"ht_m2": "minutter",
		"ht_h1": "time",
		"ht_h2": "timer",
		"ht_d1": "dag",
		"ht_d2": "dager",
		"ht_and": " og ",

		"goh": "kontrollpanel",
		"gop": 'naviger til mappen før denne">forr.',
		"gou": 'naviger ett nivå opp">opp',
		"gon": 'naviger til mappen etter denne">neste',
		"logout": "Logg ut ",
		"login": "Logg inn",
		"access": " tilgang",
		"ot_close": "lukk verktøy",
		"ot_search": "søk etter filer ved å angi filnavn, mappenavn, tid, størrelse, eller metadata som sangtittel / artist / osv.$N$N&lt;code&gt;foo bar&lt;/code&gt; = inneholder både «foo» og «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = inneholder «foo» men ikke «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = starter med «yana», filtype «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = «try unite» eksakt$N$Ndatoformat er iso-8601, så f.eks.$N&lt;code&gt;2009-12-31&lt;/code&gt; eller &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: slett filer som du nylig har lastet opp; «angre-knappen»",
		"ot_bup": "bup: tradisjonell / primitiv filopplastning,$N$Nfungerer i omtrent samtlige nettlesere",
		"ot_mkdir": "mkdir: lag en ny mappe",
		"ot_md": "new-md: lag et nytt markdown-dokument",
		"ot_msg": "msg: send en beskjed til serverloggen",
		"ot_mp": "musikkspiller-instillinger",
		"ot_cfg": "andre innstillinger",
		"ot_u2i": 'up2k: last opp filer (hvis du har skrivetilgang) eller bytt til søkemodus for å sjekke om filene finnes et-eller-annet sted på serveren$N$Nopplastninger kan gjenopptas etter avbrudd, skjer stykkevis for potensielt høyere ytelse, og ivaretar datostempling -- men bruker litt mer prosessorkraft enn [🎈]&nbsp; (den primitive opplasteren "bup")<br /><br />mens opplastninger foregår så vises fremdriften her oppe!',
		"ot_u2w": 'up2k: filopplastning med støtte for å gjenoppta avbrutte opplastninger -- steng ned nettleseren og dra de samme filene inn i nettleseren igjen for å plukke opp igjen der du slapp$N$Nopplastninger skjer stykkevis for potensielt høyere ytelse, og ivaretar datostempling -- men bruker litt mer prosessorkraft enn [🎈]&nbsp; (den primitive opplasteren "bup")<br /><br />mens opplastninger foregår så vises fremdriften her oppe!',
		"ot_noie": 'Fungerer mye bedre i Chrome / Firefox / Edge',

		"ab_mkdir": "lag mappe",
		"ab_mkdoc": "nytt dokument",
		"ab_msg": "send melding",

		"ay_path": "gå videre til mapper",
		"ay_files": "gå videre til filer",

		"wt_ren": "gi nye navn til de valgte filene$NSnarvei: F2",
		"wt_del": "slett de valgte filene$NSnarvei: ctrl-K",
		"wt_cut": "klipp ut de valgte filene &lt;small&gt;(for å lime inn et annet sted)&lt;/small&gt;$NSnarvei: ctrl-X",
		"wt_cpy": "kopiér de valgte filene til utklippstavlen$N(for å lime inn et annet sted)$NSnarvei: ctrl-C",
		"wt_pst": "lim inn filer (som tidligere ble klippet ut / kopiert et annet sted)$NSnarvei: ctrl-V",
		"wt_selall": "velg alle filer$NSnarvei: ctrl-A (mens fokus er på en fil)",
		"wt_selinv": "inverter utvalg",
		"wt_zip1": "last ned denne mappen som et arkiv",
		"wt_selzip": "last ned de valgte filene som et arkiv",
		"wt_seldl": "last ned de valgte filene$NSnarvei: Y",
		"wt_npirc": "kopiér sang-info (irc-formatert)",
		"wt_nptxt": "kopiér sang-info",
		"wt_m3ua": "legg til sang i m3u-spilleliste$N(husk å klikke på <code>📻copy</code> senere)",
		"wt_m3uc": "kopiér m3u-spillelisten til utklippstavlen",
		"wt_grid": "bytt mellom ikoner og listevisning$NSnarvei: G",
		"wt_prev": "forrige sang$NSnarvei: J",
		"wt_play": "play / pause$NSnarvei: P",
		"wt_next": "neste sang$NSnarvei: L",

		"ul_par": "samtidige handl.:",
		"ut_rand": "finn opp nye tilfeldige filnavn",
		"ut_u2ts": "gi filen på serveren samme$Ntidsstempel som lokalt hos deg\">📅",
		"ut_ow": "overskrive eksisterende filer på serveren?$N🛡️: aldri (finner på et nytt filnavn istedenfor)$N🕒: overskriv hvis serverens fil er eldre$N♻️: alltid, gitt at innholdet er forskjellig",
		"ut_mt": "fortsett å befare køen mens opplastning foregår$N$Nskru denne av dersom du har en$Ntreg prosessor eller harddisk",
		"ut_ask": 'bekreft filutvalg før opplastning starter">💭',
		"ut_pot": "forbedre ytelsen på trege enheter ved å$Nforenkle brukergrensesnittet",
		"ut_srch": "utfør søk istedenfor å laste opp --$Nleter igjennom alle mappene du har lov til å se",
		"ut_par": "sett til 0 for å midlertidig stanse opplastning$N$Nhøye verdier (4 eller 8) kan gi bedre ytelse,$Nspesielt på trege internettlinjer$N$Nbør ikke være høyere enn 1 på LAN$Neller hvis serveren sin harddisk er treg",
		"ul_btn": "slipp filer / mapper<br>her (eller klikk meg)",
		"ul_btnu": "L A S T &nbsp; O P P",
		"ul_btns": "F I L S Ø K",

		"ul_hash": "befar",
		"ul_send": "&nbsp;send",
		"ul_done": "total",
		"ul_idle1": "ingen handlinger i køen",
		"ut_etah": "snitthastighet for &lt;em&gt;befaring&lt;/em&gt; samt gjenstående tid",
		"ut_etau": "snitthastighet for &lt;em&gt;opplastning&lt;/em&gt; samt gjenstående tid",
		"ut_etat": "&lt;em&gt;total&lt;/em&gt; snitthastighet og gjenstående tid",

		"uct_ok": "fullført uten problemer",
		"uct_ng": "fullført under tvil (duplikat, ikke funnet, ...)",
		"uct_done": "fullført (enten &lt;em&gt;ok&lt;/em&gt; eller &lt;em&gt;ng&lt;/em&gt;)",
		"uct_bz": "aktive handlinger (befaring / opplastning)",
		"uct_q": "køen",

		"utl_name": "filnavn",
		"utl_ulist": "vis",
		"utl_ucopy": "kopiér",
		"utl_links": "lenker",
		"utl_stat": "status",
		"utl_prog": "fremdrift",

		// må være korte:
		"utl_404": "404",
		"utl_err": "FEIL!",
		"utl_oserr": "OS-feil",
		"utl_found": "funnet",
		"utl_defer": "senere",
		"utl_yolo": "YOLO",
		"utl_done": "ferdig",

		"ul_flagblk": "filene har blitt lagt i køen</b><br>men det er en annen nettleserfane som holder på med befaring eller opplastning akkurat nå,<br>så venter til den er ferdig først",
		"ul_btnlk": "bryteren har blitt låst til denne tilstanden i serverens konfigurasjon",

		"udt_up": "Last opp",
		"udt_srch": "Søk",
		"udt_drop": "Slipp filene her",

		"u_nav_m": '<h6>hva har du?</h6><code>Enter</code> = Filer (én eller flere)\n<code>ESC</code> = Én mappe (inkludert undermapper)',
		"u_nav_b": '<a href="#" id="modal-ok">Filer</a><a href="#" id="modal-ng">Én mappe</a>',

		"cl_opts": "brytere",
		"cl_themes": "utseende",
		"cl_langs": "språk",
		"cl_ziptype": "nedlastning av mapper",
		"cl_uopts": "up2k-brytere",
		"cl_favico": "favicon",
		"cl_bigdir": "store mapper",
		"cl_hsort": "#sort",
		"cl_keytype": "notasjon for musikalsk dur",
		"cl_hiddenc": "skjulte kolonner",
		"cl_hidec": "skjul",
		"cl_reset": "nullstill",
		"cl_hpick": "klikk på overskriften til kolonnene du ønsker å skjule i tabellen nedenfor",
		"cl_hcancel": "kolonne-skjuling avbrutt",

		"ct_grid": '田 ikoner',
		"ct_ttips": 'vis hjelpetekst ved å holde musen over ting">ℹ️ tips',
		"ct_thumb": 'vis miniatyrbilder istedenfor ikoner$NSnarvei: T">🖼️ bilder',
		"ct_csel": 'bruk tastene CTRL og SHIFT for markering av filer i ikonvisning">merk',
		"ct_ihop": 'bla ned til sist viste bilde når bildeviseren lukkes">g⮯',
		"ct_dots": 'vis skjulte filer (gitt at serveren tillater det)">.synlig',
		"ct_qdel": 'sletteknappen spør bare én gang om bekreftelse">hurtig🗑️',
		"ct_dir1st": 'sorter slik at mapper kommer foran filer">📁 først',
		"ct_nsort": 'naturlig sortering (forstår tall i filnavn)">nsort',
		"ct_utc": 'bruk UTC for alle klokkeslett">UTC',
		"ct_readme": 'vis README.md nedenfor filene">📜 readme',
		"ct_idxh": 'vis index.html istedenfor fil-liste">htm',
		"ct_sbars": 'vis rullgardiner / skrollefelt">⟊',

		"cut_umod": 'i tilfelle en fil du laster opp allerede finnes på serveren, så skal serverens tidsstempel oppdateres slik at det stemmer overens med din lokale fil (krever rettighetene write+delete)">re📅',

		"cut_turbo": "forenklet befaring ved opplastning; bør sannsynlig <em>ikke</em> skrus på:$N$Nnyttig dersom du var midt i en svær opplastning som måtte restartes av en eller annen grunn, og du vil komme igang igjen så raskt som overhodet mulig.$N$Nnår denne er skrudd på så forenkles befaringen kraftig; istedenfor å utføre en trygg sjekk på om filene finnes på serveren i god stand, så sjekkes kun om <em>filstørrelsen</em> stemmer. Så dersom en korrupt fil skulle befinne seg på serveren allerede, på samme sted med samme størrelse og navn, så blir det <em>ikke oppdaget</em>.$N$Ndet anbefales å kun benytte denne funksjonen for å komme seg raskt igjennom selve opplastningen, for så å skru den av, og til slutt &quot;laste opp&quot; de samme filene én gang til -- slik at integriteten kan verifiseres\">turbo",

		"cut_datechk": "har ingen effekt dersom turbo er avslått$N$Ngjør turbo bittelitt tryggere ved å sjekke datostemplingen på filene (i tillegg til filstørrelse)$N$N<em>burde</em> oppdage og gjenoppta de fleste ufullstendige opplastninger, men er <em>ikke</em> en fullverdig erstatning for å deaktivere turbo og gjøre en skikkelig sjekk\">date-chk",

		"cut_u2sz": "størrelse i megabyte for hvert bruddstykke for opplastning. Store verdier flyr bedre over atlanteren. Små verdier kan være bedre på særdeles ustabile forbindelser",

		"cut_flag": "samkjører nettleserfaner slik at bare én $N kan holde på med befaring / opplastning $N -- andre faner må også ha denne skrudd på $N -- fungerer kun innenfor samme domene",

		"cut_az": "last opp filer i alfabetisk rekkefølge, istedenfor minste-fil-først$N$Nalfabetisk kan gjøre det lettere å anslå om alt gikk bra, men er bittelitt tregere på fiber / LAN",

		"cut_nag": "meldingsvarsel når opplastning er ferdig$N(kun om nettleserfanen ikke er synlig)",
		"cut_sfx": "lydvarsel når opplastning er ferdig$N(kun om nettleserfanen ikke er synlig)",

		"cut_mt": "raskere befaring ved å bruke hele CPU'en$N$Ndenne funksjonen anvender web-workers$Nog krever mer RAM (opptil 512 MiB ekstra)$N$Ngjør https 30% raskere, http 4.5x raskere\">mt",

		"cut_wasm": "bruk wasm istedenfor nettleserens sha512-funksjon; gir bedre ytelse på chrome-baserte nettlesere, men bruker mere CPU, og eldre versjoner av chrome tåler det ikke (spiser opp all RAM og krasjer)\">wasm",

		"cft_text": "ikontekst (blank ut og last siden på nytt for å deaktivere)",
		"cft_fg": "farge",
		"cft_bg": "bakgrunnsfarge",

		"cdt_lim": "maks antall filer å vise per mappe",
		"cdt_ask": "vis knapper for å laste flere filer nederst på siden istedenfor å gradvis laste mer av mappen når man scroller ned",
		"cdt_hsort": "antall sorterings-regler (&lt;code&gt;,sorthref&lt;/code&gt;) som skal inkluderes når media-URL'er genereres. Hvis denne er 0 så vil sorterings-regler i URL'er hverken bli generert eller lest",

		"tt_entree": "bytt til mappehierarki$NSnarvei: B",
		"tt_detree": "bytt til tradisjonell sti-visning$NSnarvei: B",
		"tt_visdir": "bla ned til den åpne mappen",
		"tt_ftree": "bytt mellom filstruktur og tekstfiler$NSnarvei: V",
		"tt_pdock": "vis de overordnede mappene i et panel",
		"tt_dynt": "øk bredden på panelet ettersom treet utvider seg",
		"tt_wrap": "linjebryting",
		"tt_hover": "vis hele mappenavnet når musepekeren treffer mappen$N( gjør dessverre at scrollhjulet fusker dersom musepekeren ikke befinner seg i grøfta )",

		"ml_pmode": "ved enden av mappen",
		"ml_btns": "knapper",
		"ml_tcode": "konvertering",
		"ml_tcode2": "konverter til",
		"ml_tint": "tint",
		"ml_eq": "audio equalizer (tonejustering)",
		"ml_drc": "compressor (volum-utjevning)",

		"mt_loop": "spill den samme sangen om og om igjen\">🔁",
		"mt_one": "spill kun én sang\">1️⃣",
		"mt_shuf": "sangene i hver mappe$Nspilles i tilfeldig rekkefølge\">🔀",
		"mt_aplay": "forsøk å starte avspilling hvis linken du klikket på for å åpne nettsiden inneholder en sang-ID$N$Nhvis denne deaktiveres så vil heller ikke nettside-URL'en bli oppdatert med sang-ID'er når musikk spilles, i tilfelle innstillingene skulle gå tapt og nettsiden lastes på ny\">a▶",
		"mt_preload": "hent ned litt av neste sang i forkant,$Nslik at pausen i overgangen blir mindre\">forles",
		"mt_prescan": "ved behov, bla til neste mappe$Nslik at nettleseren lar oss$Nfortsette å spille musikk\">bla",
		"mt_fullpre": "hent ned hele neste sang, ikke bare litt:$N✅ skru på hvis nettet ditt er <b>ustabilt</b>,$N❌ skru av hvis nettet ditt er <b>tregt</b>\">full",
		"mt_fau": "for telefoner: forhindre at avspilling stopper hvis nettet er for tregt til å laste neste sang i tide. Hvis påskrudd, kan forårsake at sang-info ikke vises korrekt i OS'et\">☕️",
		"mt_waves": "waveform seekbar:$Nvis volumkurve i avspillingsfeltet\">~s",
		"mt_npclip": "vis knapper for å kopiere info om sangen du hører på\">/np",
		"mt_m3u_c": "vis knapper for å kopiere de valgte$Nsangene som innslag i en m3u8 spilleliste\">📻",
		"mt_octl": "integrering med operativsystemet (fjernkontroll, info-skjerm)\">os-ctl",
		"mt_oseek": "tillat spoling med fjernkontroll$N$Nmerk: på noen enheter (iPhones) så vil$Ndette erstatte knappen for neste sang\">spoling",
		"mt_oscv": "vis album-cover på infoskjermen\">bilde",
		"mt_follow": "bla slik at sangen som spilles alltid er synlig\">🎯",
		"mt_compact": "tettpakket avspillerpanel\">⟎",
		"mt_uncache": "prøv denne hvis en sang ikke spiller riktig\">oppfrisk",
		"mt_mloop": "repeter hele mappen\">🔁 gjenta",
		"mt_mnext": "hopp til neste mappe og fortsett\">📂 neste",
		"mt_mstop": "stopp avspilling\">⏸ stopp",
		"mt_cflac": "konverter flac / wav-filer til {0}\">flac",
		"mt_caac": "konverter aac / m4a-filer til to {0}\">aac",
		"mt_coth": "konverter alt annet (men ikke mp3) til {0}\">andre",
		"mt_c2opus": "det beste valget for alle PCer og Android\">opus",
		"mt_c2owa": "opus-weba, for iOS 17.5 og nyere\">owa",
		"mt_c2caf": "opus-caf, for iOS 11 tilogmed 17\">caf",
		"mt_c2mp3": "bra valg for steinalder-utstyr (slår aldri feil)\">mp3",
		"mt_c2flac": "gir best lydkvalitet, men eter nettet ditt\">flac",
		"mt_c2wav": "helt rå lydstrøm (bruker enda mere data enn flac)\">wav",
		"mt_c2ok": "bra valg!",
		"mt_c2nd": "ikke det foretrukne valget for din enhet, men funker sikkert greit",
		"mt_c2ng": "ser virkelig ikke ut som enheten din takler dette formatet... men ok, vi prøver",
		"mt_xowa": "iOS har fortsatt problemer med avspilling av owa-musikk i bakgrunnen. Bruk caf eller mp3 istedenfor",
		"mt_tint": "nivå av bakgrunnsfarge på søkestripa (0-100),$Ngjør oppdateringer mindre distraherende",
		"mt_eq": "aktiver tonekontroll og forsterker;$N$Nboost &lt;code&gt;0&lt;/code&gt; = normal volumskala$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = normal stereo$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% blanding venstre-høyre$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = instrumental :^)$N$Nreduserer også dødtid imellom sangfiler",
		"mt_drc": "aktiver volum-utjevning (dynamic range compressor); vil også aktivere tonejustering, så sett alle EQ-feltene bortsett fra 'width' til 0 hvis du ikke vil ha noe EQ$N$Nfilteret vil dempe volumet på alt som er høyere enn TRESH dB; for hver RATIO dB over grensen er det 1dB som treffer høyttalerne, så standardverdiene tresh -24 og ratio 12 skal bety at volumet ikke går høyere enn -22 dB, slik at man trygt kan øke boost-verdien i equalizer'n til rundt 0.8, eller 1.8 kombinert med ATK 0 og RLS 90 (bare mulig i firefox; andre nettlesere tar ikke høyere RLS enn 1)$N$Nwikipedia forklarer dette mye bedre forresten",

		"mb_play": "lytt",
		"mm_hashplay": "spill denne sangen?",
		"mm_m3u": "trykk <code>Enter/OK</code> for å spille\ntrykk <code>ESC/Avbryt</code> for å redigere",
		"mp_breq": "krever firefox 82+, chrome 73+, eller iOS 15+",
		"mm_bload": "laster inn...",
		"mm_bconv": "konverterer til {0}, vent litt...",
		"mm_opusen": "nettleseren din forstår ikke aac / m4a;\nkonvertering til opus er nå aktivert",
		"mm_playerr": "avspilling feilet: ",
		"mm_eabrt": "Avspillingsforespørselen ble avbrutt",
		"mm_enet": "Nettet ditt er ustabilt",
		"mm_edec": "Noe er galt med musikkfilen",
		"mm_esupp": "Nettleseren din forstår ikke filtypen",
		"mm_eunk": "Ukjent feil",
		"mm_e404": "Avspilling feilet: Fil ikke funnet.",
		"mm_e403": "Avspilling feilet: Tilgang nektet.\n\nKanskje du ble logget ut?\nPrøv å trykk F5 for å laste siden på nytt.",
		"mm_e500": "Avspilling feilet: Rusk i maskineriet, sjekk serverloggen.",
		"mm_e5xx": "Avspilling feilet: ",
		"mm_nof": "finner ikke flere sanger i nærheten",
		"mm_prescan": "Leter etter neste sang...",
		"mm_scank": "Fant neste sang:",
		"mm_uncache": "alle sanger vil lastes på nytt ved neste avspilling",
		"mm_hnf": "sangen finnes ikke lenger",

		"im_hnf": "bildet finnes ikke lenger",

		"f_empty": 'denne mappen er tom',
		"f_chide": 'dette vil skjule kolonnen «{0}»\n\nfanen for "andre innstillinger" lar deg vise kolonnen igjen',
		"f_bigtxt": "denne filen er hele {0} MiB -- vis som tekst?",
		"f_bigtxt2": "vil du se bunnen av filen istedenfor? du vil da også se nye linjer som blir lagt til på slutten av filen i sanntid",
		"fbd_more": '<div id="blazy">viser <code>{0}</code> av <code>{1}</code> filer; <a href="#" id="bd_more">vis {2}</a> eller <a href="#" id="bd_all">vis alle</a></div>',
		"fbd_all": '<div id="blazy">viser <code>{0}</code> av <code>{1}</code> filer; <a href="#" id="bd_all">vis alle</a></div>',
		"f_anota": "kun {0} av totalt {1} elementer ble markert;\nfor å velge alt må du bla til bunnen av mappen først",

		"f_dls": 'linkene i denne mappen er nå\nomgjort til nedlastningsknapper',

		"f_partial": "For å laste ned en fil som enda ikke er ferdig opplastet, klikk på filen som har samme filnavn som denne, men uten <code>.PARTIAL</code> på slutten. Da vil serveren passe på at nedlastning går bra. Derfor anbefales det sterkt å trykke AVBRYT eller Escape-tasten.\n\nHvis du virkelig ønsker å laste ned denne <code>.PARTIAL</code>-filen på en ukontrollert måte, trykk OK / Enter for å ignorere denne advarselen. Slik vil du høyst sannsynlig motta korrupt data.",

		"ft_paste": "Lim inn {0} filer$NSnarvei: ctrl-V",
		"fr_eperm": 'kan ikke endre navn:\ndu har ikke “move”-rettigheten i denne mappen',
		"fd_eperm": 'kan ikke slette:\ndu har ikke “delete”-rettigheten i denne mappen',
		"fc_eperm": 'kan ikke klippe ut:\ndu har ikke “move”-rettigheten i denne mappen',
		"fp_eperm": 'kan ikke lime inn:\ndu har ikke “write”-rettigheten i denne mappen',
		"fr_emore": "velg minst én fil som skal få nytt navn",
		"fd_emore": "velg minst én fil som skal slettes",
		"fc_emore": "velg minst én fil som skal klippes ut",
		"fcp_emore": "velg minst én fil som skal kopieres til utklippstavlen",

		"fs_sc": "del mappen du er i nå",
		"fs_ss": "del de valgte filene",
		"fs_just1d": "du kan ikke markere flere mapper samtidig,\neller kombinere mapper og filer",
		"fs_abrt": "❌ avbryt",
		"fs_rand": "🎲 tilfeldig navn",
		"fs_go": "✅ opprett deling",
		"fs_name": "navn",
		"fs_src": "kilde",
		"fs_pwd": "passord",
		"fs_exp": "varighet",
		"fs_tmin": "min",
		"fs_thrs": "timer",
		"fs_tdays": "dager",
		"fs_never": "for evig",
		"fs_pname": "frivillig navn (blir noe tilfeldig ellers)",
		"fs_tsrc": "fil/mappe som skal deles",
		"fs_ppwd": "frivillig passord",
		"fs_w8": "oppretter deling...",
		"fs_ok": "trykk <code>Enter/OK</code> for å kopiere linken (for CTRL-V)\ntrykk <code>ESC/Avbryt</code> for å bare bekrefte",

		"frt_dec": "kan korrigere visse ødelagte filnavn\">url-decode",
		"frt_rst": "nullstiller endringer (tilbake til de originale filnavnene)\">↺ reset",
		"frt_abrt": "avbryt og lukk dette vinduet\">❌ avbryt",
		"frb_apply": "IVERKSETT",
		"fr_adv": "automasjon basert på metadata<br>og / eller mønster (regulære uttrykk)\">avansert",
		"fr_case": "versalfølsomme uttrykk\">Aa",
		"fr_win": "bytt ut bokstavene <code>&lt;&gt;:&quot;\\|?*</code> med$Ntilsvarende som windows ikke får panikk av\">win",
		"fr_slash": "bytt ut bokstaven <code>/</code> slik at den ikke forårsaker at nye mapper opprettes\">ikke /",
		"fr_re": "regex-mønster som kjøres på hvert filnavn. Grupper kan leses ut i format-feltet nedenfor, f.eks. &lt;code&gt;(1)&lt;/code&gt; og &lt;code&gt;(2)&lt;/code&gt; osv.",
		"fr_fmt": "inspirert av foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; byttes ut med sangtittel,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; dropper [dette] hvis artist er blank$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; viser sangnr. med 2 siffer",
		"fr_pdel": "slett",
		"fr_pnew": "lagre som",
		"fr_pname": "gi innstillingene dine et navn",
		"fr_aborted": "avbrutt",
		"fr_lold": "gammelt navn",
		"fr_lnew": "nytt navn",
		"fr_tags": "metadata for de valgte filene (kun for referanse):",
		"fr_busy": "endrer navn på {0} filer...\n\n{1}",
		"fr_efail": "endring av navn feilet:\n",
		"fr_nchg": "{0} av navnene ble justert pga. <code>win</code> og/eller <code>ikke /</code>\n\nvil du fortsette med de nye navnene som ble valgt?",

		"fd_ok": "sletting OK",
		"fd_err": "sletting feilet:\n",
		"fd_none": "ingenting ble slettet; kanskje avvist av serverkonfigurasjon (xbd)?",
		"fd_busy": "sletter {0} filer...\n\n{1}",
		"fd_warn1": "SLETT disse {0} filene?",
		"fd_warn2": "<b>Siste sjanse!</b> Dette kan ikke angres. Slett?",

		"fc_ok": "klippet ut {0} filer",
		"fc_warn": 'klippet ut {0} filer\n\nmen: kun <b>denne</b> nettleserfanen har mulighet til å lime dem inn et annet sted, siden antallet filer er helt hinsides',

		"fcc_ok": "kopierte {0} filer til utklippstavlen",
		"fcc_warn": 'kopierte {0} filer til utklippstavlen\n\nmen: kun <b>denne</b> nettleserfanen har mulighet til å lime dem inn et annet sted, siden antallet filer er helt hinsides',

		"fp_apply": "bekreft og lim inn nå",
		"fp_ecut": "du må klippe ut eller kopiere noen filer / mapper først\n\nmerk: du kan gjerne jobbe på kryss av nettleserfaner; klippe ut i én fane, lime inn i en annen",
		"fp_ename": "{0} filer kan ikke flyttes til målmappen fordi det allerede finnes filer med samme navn. Gi dem nye navn nedenfor, eller gi dem et blankt navn for å hoppe over dem:",
		"fcp_ename": "{0} filer kan ikke kopieres til målmappen fordi det allerede finnes filer med samme navn. Gi dem nye navn nedenfor, eller gi dem et blankt navn for å hoppe over dem:",
		"fp_emore": "det er fortsatt flere navn som må endres",
		"fp_ok": "flytting OK",
		"fcp_ok": "kopiering OK",
		"fp_busy": "flytter {0} filer...\n\n{1}",
		"fcp_busy": "kopierer {0} filer...\n\n{1}",
		"fp_abrt": "avbryter...",
		"fp_err": "flytting feilet:\n",
		"fcp_err": "kopiering feilet:\n",
		"fp_confirm": "flytt disse {0} filene hit?",
		"fcp_confirm": "kopiér disse {0} filene hit?",
		"fp_etab": 'kunne ikke lese listen med filer ifra den andre nettleserfanen',
		"fp_name": "Laster opp én fil fra enheten din. Velg filnavn:",
		"fp_both_m": '<h6>hva skal limes inn her?</h6><code>Enter</code> = Flytt {0} filer fra «{1}»\n<code>ESC</code> = Last opp {2} filer fra enheten din',
		"fcp_both_m": '<h6>hva skal limes inn her?</h6><code>Enter</code> = Kopiér {0} filer fra «{1}»\n<code>ESC</code> = Last opp {2} filer fra enheten din',
		"fp_both_b": '<a href="#" id="modal-ok">Flytt</a><a href="#" id="modal-ng">Last opp</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopiér</a><a href="#" id="modal-ng">Last opp</a>',

		"mk_noname": "skriv inn et navn i tekstboksen til venstre først :p",

		"tv_load": "Laster inn tekstfil:\n\n{0}\n\n{1}% ({2} av {3} MiB lastet ned)",
		"tv_xe1": "kunne ikke laste tekstfil:\n\nfeil ",
		"tv_xe2": "404, Fil ikke funnet",
		"tv_lst": "tekstfiler i mappen",
		"tvt_close": "gå tilbake til mappen$NSnarvei: M (eller Esc)\">❌ lukk",
		"tvt_dl": "last ned denne filen$NSnarvei: Y\">💾 last ned",
		"tvt_prev": "vis forrige dokument$NSnarvei: i\">⬆ forr.",
		"tvt_next": "vis neste dokument$NSnarvei: K\">⬇ neste",
		"tvt_sel": "markér filen &nbsp; ( for utklipp / sletting / ... )$NSnarvei: S\">merk",
		"tvt_edit": "redigér filen$NSnarvei: E\">✏️ endre",
		"tvt_tail": "overvåk filen for endringer og vis nye linjer i sanntid\">📡 følg",
		"tvt_wrap": "tekstbryting\">↵",
		"tvt_atail": "hold de nyeste linjene synlig (lås til bunnen av siden)\">⚓",
		"tvt_ctail": "forstå og vis terminalfarger (ansi-sekvenser)\">🌈",
		"tvt_ntail": "maks-grense for antall bokstaver som skal vises i vinduet",

		"m3u_add1": "sangen ble lagt til i m3u-spillelisten",
		"m3u_addn": "{0} sanger ble lagt til i m3u-spillelisten",
		"m3u_clip": "m3u-spillelisten ble kopiert til utklippstavlen\n\nneste steg er å opprette et tekstdokument med filnavn som slutter på <code>.m3u</code> og lime inn spillelisten der",

		"gt_vau": "ikke vis videofiler, bare spill lyden\">🎧",
		"gt_msel": "markér filer istedenfor å åpne dem; ctrl-klikk filer for å overstyre$N$N&lt;em&gt;når aktiv: dobbelklikk en fil / mappe for å åpne&lt;/em&gt;$N$NSnarvei: S\">markering",
		"gt_crop": "beskjær ikonene så de passer bedre\">✂",
		"gt_3x": "høyere oppløsning på ikoner\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "trim",
		"gt_sort": "sorter",
		"gt_name": "navn",
		"gt_sz": "størr.",
		"gt_ts": "dato",
		"gt_ext": "type",
		"gt_c1": "reduser maks-lengde på filnavn",
		"gt_c2": "øk maks-lengde på filnavn",

		"sm_w8": "søker...",
		"sm_prev": "søkeresultatene er fra et tidligere søk:\n  ",
		"sl_close": "lukk søkeresultater",
		"sl_hits": "viser {0} treff",
		"sl_moar": "hent flere",

		"s_sz": "størr.",
		"s_dt": "dato",
		"s_rd": "sti",
		"s_fn": "navn",
		"s_ta": "meta",
		"s_ua": "up@",
		"s_ad": "avns.",
		"s_s1": "større enn ↓ MiB",
		"s_s2": "mindre enn ↓ MiB",
		"s_d1": "nyere enn &lt;dato&gt;",
		"s_d2": "eldre enn",
		"s_u1": "lastet opp etter",
		"s_u2": "og/eller før",
		"s_r1": "mappenavn inneholder",
		"s_f1": "filnavn inneholder",
		"s_t1": "sang-info inneholder",
		"s_a1": "konkrete egenskaper",

		"md_eshow": "viser forenklet ",
		"md_off": "[📜<em>readme</em>] er avskrudd i [⚙️] -- dokument skjult",

		"badreply": "Ugyldig svar ifra serveren",

		"xhr403": "403: Tilgang nektet\n\nkanskje du ble logget ut? prøv å trykk F5",
		"xhr0": "ukjent (enten nettverksproblemer eller serverkrasj)",
		"cf_ok": "beklager -- liten tilfeldig kontroll, alt OK\n\nting skal fortsette om ca. 30 sekunder\n\nhvis ikkeno skjer, trykk F5 for å laste siden på nytt",
		"tl_xe1": "kunne ikke hente undermapper:\n\nfeil ",
		"tl_xe2": "404: Mappen finnes ikke",
		"fl_xe1": "kunne ikke hente filer i mappen:\n\nfeil ",
		"fl_xe2": "404: Mappen finnes ikke",
		"fd_xe1": "kan ikke opprette ny mappe:\n\nfeil ",
		"fd_xe2": "404: Den overordnede mappen finnes ikke",
		"fsm_xe1": "kunne ikke sende melding:\n\nfeil ",
		"fsm_xe2": "404: Den overordnede mappen finnes ikke",
		"fu_xe1": "kunne ikke hente listen med nylig opplastede filer ifra serveren:\n\nfeil ",
		"fu_xe2": "404: Filen finnes ikke??",

		"fz_tar": "ukomprimert gnu-tar arkiv, for linux og mac",
		"fz_pax": "ukomprimert pax-tar arkiv, litt tregere",
		"fz_targz": "gnu-tar pakket med gzip (nivå 3)$N$NNB: denne er veldig treg;$Nukomprimert tar er bedre",
		"fz_tarxz": "gnu-tar pakket med xz (nivå 1)$N$NNB: denne er veldig treg;$Nukomprimert tar er bedre",
		"fz_zip8": "zip med filnavn i utf8 (noe problematisk på windows 7 og eldre)",
		"fz_zipd": "zip med filnavn i cp437, for høggamle maskiner",
		"fz_zipc": "cp437 med tidlig crc32,$Nfor MS-DOS PKZIP v2.04g (oktober 1993)$N(øker behandlingstid på server)",

		"un_m1": "nedenfor kan du angre / slette filer som du nylig har lastet opp, eller avbryte ufullstendige opplastninger",
		"un_upd": "oppdater",
		"un_m4": "eller hvis du vil dele nedlastnings-lenkene:",
		"un_ulist": "vis",
		"un_ucopy": "kopiér",
		"un_flt": "valgfritt filter:&nbsp; filnavn / filsti må inneholde",
		"un_fclr": "nullstill filter",
		"un_derr": 'unpost-sletting feilet:\n',
		"un_f5": 'noe gikk galt, prøv å oppdatere listen eller trykk F5',
		"un_uf5": "beklager, men du må laste siden på nytt (f.eks. ved å trykke F5 eller CTRL-R) før denne opplastningen kan avbrytes",
		"un_nou": '<b>advarsel:</b> kan ikke vise ufullstendige opplastninger akkurat nå; klikk på oppdater-linken om litt',
		"un_noc": '<b>advarsel:</b> angring av fullførte opplastninger er deaktivert i serverkonfigurasjonen',
		"un_max": "viser de første 2000 filene (bruk filteret for å innsnevre)",
		"un_avail": "{0} nylig opplastede filer kan slettes<br />{1} ufullstendige opplastninger kan avbrytes",
		"un_m2": "sortert etter opplastningstid; nyeste først:",
		"un_no1": "men nei, her var det jaggu ikkeno som slettes kan",
		"un_no2": "men nei, her var det jaggu ingenting som passet overens med filteret",
		"un_next": "slett de neste {0} filene nedenfor",
		"un_abrt": "avbryt",
		"un_del": "slett",
		"un_m3": "henter listen med nylig opplastede filer...",
		"un_busy": "sletter {0} filer...",
		"un_clip": "{0} lenker kopiert til utklippstavlen",

		"u_https1": "du burde",
		"u_https2": "bytte til https",
		"u_https3": "for høyere hastighet",
		"u_ancient": 'nettleseren din er prehistorisk -- mulig du burde <a href="#" onclick="goto(\'bup\')">bruke bup istedenfor</a>',
		"u_nowork": "krever firefox 53+, chrome 57+, eller iOS 11+",
		"tail_2old": "krever firefox 105+, chrome 71+, eller iOS 14.5+",
		"u_nodrop": 'nettleseren din er for gammel til å laste opp filer ved å dra dem inn i vinduet',
		"u_notdir": "mottok ikke mappen!\n\nnettleseren din er for gammel,\nprøv å dra mappen inn i vinduet istedenfor",
		"u_uri": "for å laste opp bilder ifra andre nettleservinduer,\nslipp bildet rett på den store last-opp-knappen",
		"u_enpot": 'bytt til <a href="#">enkelt UI</a> (gir sannsynlig raskere opplastning)',
		"u_depot": 'bytt til <a href="#">snæsent UI</a> (gir sannsynlig tregere opplastning)',
		"u_gotpot": 'byttet til et enklere UI for å laste opp raskere,\n\ndu kan gjerne bytte tilbake altså!',
		"u_pott": "<p>filer: &nbsp; <b>{0}</b> ferdig, &nbsp; <b>{1}</b> feilet, &nbsp; <b>{2}</b> behandles, &nbsp; <b>{3}</b> i kø</p>",
		"u_ever": "dette er den primitive opplasteren; up2k krever minst:<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'dette er den primitive opplasteren; <a href="#" id="u2yea">up2k</a> er bedre',
		"u_uput": 'litt raskere (uten sha512)',
		"u_ewrite": 'du har ikke skrivetilgang i denne mappen',
		"u_eread": 'du har ikke lesetilgang i denne mappen',
		"u_enoi": 'filsøk er deaktivert i serverkonfigurasjonen',
		"u_enoow": "kan ikke overskrive filer her (Delete-rettigheten er nødvendig)",
		"u_badf": 'Disse {0} filene (av totalt {1}) kan ikke leses, kanskje pga rettighetsproblemer i filsystemet på datamaskinen din:\n\n',
		"u_blankf": 'Disse {0} filene (av totalt {1}) er blanke / uten innhold; ønsker du å laste dem opp uansett?\n\n',
		"u_applef": 'Disse {0} filene (av totalt {1}) er antagelig uønskede;\nTrykk <code>OK/Enter</code> for å HOPPE OVER disse filene,\nTrykk <code>Avbryt/ESC</code> for å LASTE OPP disse filene også:\n\n',
		"u_just1": '\nFunker kanskje bedre hvis du bare tar én fil om gangen',
		"u_ff_many": 'Hvis du bruker <b>Linux / MacOS / Android,</b> så kan dette antallet filer<br /><a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank"><em>kanskje</em> krasje Firefox!</a> Hvis det skjer, så prøv igjen (eller bruk Chrome).',
		"u_up_life": "Filene slettes fra serveren {0}\netter at opplastningen er fullført",
		"u_asku": 'Laste opp disse {0} filene til <code>{1}</code>',
		"u_unpt": "Du kan angre / slette opplastningen med 🧯 oppe til venstre",
		"u_bigtab": 'Vil nå vise {0} filer...\n\nDette kan krasje nettleseren din. Fortsette?',
		"u_scan": 'Leser mappene...',
		"u_dirstuck": 'Nettleseren din fikk ikke tilgang til å lese følgende {0} filer/mapper, så de blir hoppet over:',
		"u_etadone": 'Ferdig ({0}, {1} filer)',
		"u_etaprep": '(forbereder opplastning)',
		"u_hashdone": 'befaring ferdig',
		"u_hashing": 'les',
		"u_hs": 'serveren tenker...',
		"u_started": "filene blir nå lastet opp 🚀",
		"u_dupdefer": "duplikat; vil bli håndtert til slutt",
		"u_actx": "klikk her for å forhindre tap av<br />ytelse ved bytte til andre vinduer/faner",
		"u_fixed": "OK!&nbsp; Løste seg 👍",
		"u_cuerr": "kunne ikke laste opp del {0} av {1};\nsikkert greit, fortsetter\n\nfil: {2}",
		"u_cuerr2": "server nektet opplastningen (del {0} av {1});\nprøver igjen senere\n\nfil: {2}\n\nerror ",
		"u_ehstmp": "prøver igjen; se mld nederst",
		"u_ehsfin": "server nektet forespørselen om å ferdigstille filen; prøver igjen...",
		"u_ehssrch": "server nektet forespørselen om å utføre søk; prøver igjen...",
		"u_ehsinit": "server nektet forespørselen om å begynne en ny opplastning; prøver igjen...",
		"u_eneths": "et problem med nettverket gjorde at avtale om opplastning ikke kunne inngås; prøver igjen...",
		"u_enethd": "et problem med nettverket gjorde at filsjekk ikke kunne utføres; prøver igjen...",
		"u_cbusy": "venter på klarering ifra server etter et lite nettverksglipp...",
		"u_ehsdf": "serveren er full!\n\nprøver igjen regelmessig,\ni tilfelle noen rydder litt...",
		"u_emtleak1": "uff, det er mulig at nettleseren din har en minnelekkasje...\nForeslår",
		"u_emtleak2": ' helst at du <a href="{0}">bytter til https</a>, eller ',
		"u_emtleak3": ' at du ',
		"u_emtleakc": 'prøver følgende:\n<ul><li>trykk F5 for å laste siden på nytt</li><li>så skru av &nbsp;<code>mt</code>&nbsp; bryteren under &nbsp;<code>⚙️ innstillinger</code></li><li>og forsøk den samme opplastningen igjen</li></ul>Opplastning vil gå litt tregere, men det får så være.\nBeklager bryderiet !\n\nPS: feilen <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">skal være fikset</a> i chrome v107',
		"u_emtleakf": 'prøver følgende:\n<ul><li>trykk F5 for å laste siden på nytt</li><li>så skru på <code>🥔</code> ("enkelt UI") i opplasteren</li><li>og forsøk den samme opplastningen igjen</li></ul>\nPS: Firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">fikser forhåpentligvis feilen</a> en eller annen gang',
		"u_s404": "ikke funnet på serveren",
		"u_expl": "forklar",
		"u_maxconn": "de fleste nettlesere tillater ikke mer enn 6, men firefox lar deg øke grensen med <code>connections-per-server</code> i <code>about:config</code>",
		"u_tu": '<p class="warn">ADVARSEL: turbo er på, <span>&nbsp;avbrutte opplastninger vil muligens ikke oppdages og gjenopptas; hold musepekeren over turbo-knappen for mer info</span></p>',
		"u_ts": '<p class="warn">ADVARSEL: turbo er på, <span>&nbsp;søkeresultater kan være feil; hold musepekeren over turbo-knappen for mer info</span></p>',
		"u_turbo_c": "turbo er deaktivert i serverkonfigurasjonen",
		"u_turbo_g": 'turbo ble deaktivert fordi du ikke har\ntilgang til å se mappeinnhold i dette volumet',
		"u_life_cfg": 'slett opplastning etter <input id="lifem" p="60" /> min (eller <input id="lifeh" p="3600" /> timer)',
		"u_life_est": 'opplastningen slettes <span id="lifew" tt="lokal tid">---</span>',
		"u_life_max": 'denne mappen tillater ikke å \noppbevare filer i mer enn {0}',
		"u_unp_ok": 'opplastning kan angres i {0}',
		"u_unp_ng": 'opplastning kan IKKE angres',
		"ue_ro": 'du har ikke skrivetilgang i denne mappen\n\n',
		"ue_nl": 'du er ikke logget inn',
		"ue_la": 'du er logget inn som "{0}"',
		"ue_sr": 'du er i filsøk-modus\n\nbytt til opplastning ved å klikke på forstørrelsesglasset 🔎 (ved siden av den store FILSØK-knappen) og prøv igjen\n\nsorry',
		"ue_ta": 'prøv å laste opp igjen, det burde funke nå',
		"ue_ab": "den samme filen er allerede under opplastning til en annen mappe, og den må fullføres der før filen kan lastes opp andre steder.\n\nDu kan avbryte og glemme den påbegynte opplastningen ved hjelp av 🧯 oppe til venstre",
		"ur_1uo": "OK: Filen ble lastet opp",
		"ur_auo": "OK: Alle {0} filene ble lastet opp",
		"ur_1so": "OK: Filen ble funnet på serveren",
		"ur_aso": "OK: Alle {0} filene ble funnet på serveren",
		"ur_1un": "Opplastning feilet!",
		"ur_aun": "Alle {0} opplastningene gikk feil!",
		"ur_1sn": "Filen finnes IKKE på serveren",
		"ur_asn": "Fant INGEN av de {0} filene på serveren",
		"ur_um": "Ferdig;\n{0} opplastninger gikk bra,\n{1} opplastninger gikk feil",
		"ur_sm": "Ferdig;\n{0} filer ble funnet,\n{1} filer finnes IKKE på serveren",

		"lang_set": "passer det å laste siden på nytt?",
	},
	"chi": {
		// 以 //m 结尾的行是未经验证的机器翻译
		"tt": "中文",
		"cols": {
			"c": "操作按钮",
			"dur": "持续时间",
			"q": "质量 / 比特率",
			"Ac": "音频编码",
			"Vc": "视频编码",
			"Fmt": "格式 / 容器",
			"Ahash": "音频校验和",
			"Vhash": "视频校验和",
			"Res": "分辨率",
			"T": "文件类型",
			"aq": "音频质量 / 比特率",
			"vq": "视频质量 / 比特率",
			"pixfmt": "子采样 / 像素结构",
			"resw": "水平分辨率",
			"resh": "垂直分辨率",
			"chs": "音频频道",
			"hz": "采样率"
		},

		"hks": [
			[
				"misc",
				["ESC", "关闭各种窗口"],

				"file-manager",
				["G", "切换列表 / 网格视图"],
				["T", "切换缩略图 / 图标"],
				["⇧ A/D", "缩略图大小"],
				["ctrl-K", "删除选中项"],
				["ctrl-X", "剪切选中项"],
				["ctrl-C", "复制选中项"], //m
				["ctrl-V", "粘贴到文件夹"],
				["Y", "下载选中项"],
				["F2", "重命名选中项"],

				"file-list-sel",
				["space", "切换文件选择"],
				["↑/↓", "移动选择光标"],
				["ctrl ↑/↓", "移动光标和视图"],
				["⇧ ↑/↓", "选择上一个/下一个文件"],
				["ctrl-A", "选择所有文件 / 文件夹"]
			], [
				"navigation",
				["B", "切换面包屑导航 / 导航窗格"],
				["I/K", "前一个/下一个文件夹"],
				["M", "父文件夹（或折叠当前文件夹）"],
				["V", "切换导航窗格中的文件夹 / 文本文件"],
				["A/D", "导航窗格大小"]
			], [
				"audio-player",
				["J/L", "上一首/下一首歌曲"],
				["U/O", "跳过10秒向前/向后"],
				["0..9", "跳转到0%..90%"],
				["P",  "播放/暂停（也可以启动）"],
				["S", "选择正在播放的歌曲"], //m
				["Y", "下载歌曲"]
			], [
				"image-viewer",
				["J/L, ←/→", "上一张/下一张图片"],
				["Home/End", "第一张/最后一张图片"],
				["F", "全屏"],
				["R", "顺时针旋转"],
				["⇧ R", "逆时针旋转"],
				["S", "选择图片"], //m
				["Y", "下载图片"]
			], [
				"video-player",
				["U/O", "跳过10秒向前/向后"],
				["P/K/Space", "播放/暂停"],
				["C", "继续播放下一段"],
				["V", "循环"],
				["M", "静音"],
				["[ and ]", "设置循环区间"]
			], [
				"textfile-viewer",
				["I/K", "前一个/下一个文件"],
				["M", "关闭文本文件"],
				["E", "编辑文本文件"],
				["S", "选择文件（用于剪切/重命名）"]
			]
		],

		"m_ok": "确定",
		"m_ng": "取消",

		"enable": "启用",
		"danger": "危险",
		"clipped": "已复制到剪贴板",

		"ht_s1": "秒",
		"ht_s2": "秒",
		"ht_m1": "分",
		"ht_m2": "分",
		"ht_h1": "时",
		"ht_h2": "时",
		"ht_d1": "天",
		"ht_d2": "天",
		"ht_and": " 和 ",

		"goh": "控制面板",
		"gop": '前一项">pre',
		"gou": '顶部">up',
		"gon": '下一项">next',
		"logout": " 登出",
		"login": "登录", //m
		"access": " 访问",
		"ot_close": "关闭子菜单",
		"ot_search": "按属性、路径/名称、音乐标签或上述内容的任意组合搜索文件$N$N&lt;code&gt;foo bar&lt;/code&gt; = 必须包含 «foo» 和 «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = 包含 «foo» 而不包含 «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = 以 «yama» 为开头的 «opus» 文件$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = 正好包含 «try unite»$N$N时间格式为 iso-8601, 比如:$N&lt;code&gt;2009-12-31&lt;/code&gt; or &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "取消发布：删除最近上传的内容，或中止未完成的内容",
		"ot_bup": "bup：基础上传器，甚至支持 Netscape 4.0",
		"ot_mkdir": "mkdir：创建新目录",
		"ot_md": "new-md：创建新 Markdown 文档",
		"ot_msg": "msg：向服务器日志发送消息",
		"ot_mp": "媒体播放器选项",
		"ot_cfg": "配置选项",
		"ot_u2i": 'up2k：上传文件（如果你有写入权限），或切换到搜索模式以查看文件是否存在于服务器上,$N$N上传是可恢复的，多线程的，保留文件时间戳，但比 [🎈]&nbsp;（基础上传器）占用 更多的CPU<br /><br />上传过程中，此图标会变成进度指示器！',
		"ot_u2w": 'up2k：带有恢复支持的文件上传（关闭浏览器后，重新上传相同文件）$N$N多线程的，文件时间戳得以保留，但比 [🎈]&nbsp; （基础上传器）使用更多CPU<br /><br />上传过程中，这个图标会变成进度指示器！',
		"ot_noie": '请使用 Chrome / Firefox / Edge',

		"ab_mkdir": "创建目录",
		"ab_mkdoc": "新建 Markdown 文档",
		"ab_msg": "发送消息到服务器日志",

		"ay_path": "跳转到文件夹",
		"ay_files": "跳转到文件",

		"wt_ren": "重命名选中的项目$N快捷键: F2",
		"wt_del": "删除选中的项目$N快捷键: ctrl-K",
		"wt_cut": "剪切选中的项目&lt;small&gt;（然后粘贴到其他地方）&lt;/small&gt;$N快捷键: ctrl-X",
		"wt_cpy": "将选中的项目复制到剪贴板&lt;small&gt;（然后粘贴到其他地方）&lt;/small&gt;$N快捷键: ctrl-C", //m
		"wt_pst": "粘贴之前剪切/复制的选择$N快捷键: ctrl-V",
		"wt_selall": "选择所有文件$N快捷键: ctrl-A（当文件被聚焦时）",
		"wt_selinv": "反转选择",
		"wt_zip1": "将此文件夹下载为归档文件", //m
		"wt_selzip": "将选择下载为归档文件",
		"wt_seldl": "将选择下载为单独的文件$N快捷键: Y",
		"wt_npirc": "复制 IRC 格式的曲目信息",
		"wt_nptxt": "复制纯文本格式的曲目信息",
		"wt_m3ua": "添加到 m3u 播放列表（稍后点击 <code>📻copy</code>）", //m
		"wt_m3uc": "复制 m3u 播放列表到剪贴板", //m
		"wt_grid": "切换网格/列表视图$N快捷键: G",
		"wt_prev": "上一曲$N快捷键: J",
		"wt_play": "播放/暂停$N快捷键: P",
		"wt_next": "下一曲$N快捷键: L",

		"ul_par": "并行上传：",
		"ut_rand": "随机化文件名",
		"ut_u2ts": "将最后修改的时间戳$N从你的文件系统复制到服务器\">📅",
		"ut_ow": "覆盖服务器上的现有文件？$N🛡️: 从不（会生成一个新文件名）$N🕒: 服务器文件较旧则覆盖$N♻️: 总是覆盖，如果文件内容不同", //m
		"ut_mt": "在上传时继续哈希其他文件$N$N如果你的 CPU 或硬盘是瓶颈，可能需要禁用",
		"ut_ask": '上传开始前询问确认">💭',
		"ut_pot": "通过简化 UI 来$N提高慢设备上的上传速度",
		"ut_srch": "实际不上传，而是检查文件是否$N已经存在于服务器上（将扫描你可以读取的所有文件夹）",
		"ut_par": "通过将其设置为 0 来暂停上传$N$N如果你的连接很慢/延迟高，$N$N请增加在局域网或服务器硬盘是瓶颈时保持为 1",
		"ul_btn": "将文件/文件夹拖放到这里（或点击我）",
		"ul_btnu": "上 传",
		"ul_btns": "搜 索",

		"ul_hash": "哈希",
		"ul_send": "发送",
		"ul_done": "完成",
		"ul_idle1": "没有排队的上传任务",
		"ut_etah": "平均 &lt;em&gt;hashing&lt;/em&gt; 速度和估计完成时间",
		"ut_etau": "平均 &lt;em&gt;上传&lt;/em&gt; 速度和估计完成时间",
		"ut_etat": "平均 &lt;em&gt;总&lt;/em&gt; 速度和估计完成时间",

		"uct_ok": "成功完成",
		"uct_ng": "失败/拒绝/未找到",
		"uct_done": "成功和失败的组合",
		"uct_bz": "正在哈希或上传",
		"uct_q": "空闲，待处理",

		"utl_name": "文件名",
		"utl_ulist": "列表",
		"utl_ucopy": "复制",
		"utl_links": "链接",
		"utl_stat": "状态",
		"utl_prog": "进度",

		// 保持简短:
		"utl_404": "404",
		"utl_err": "错误",
		"utl_oserr": "OS错误",
		"utl_found": "已找到",
		"utl_defer": "延期",
		"utl_yolo": "加速",
		"utl_done": "完成",

		"ul_flagblk": "文件已添加到队列</b><br>但另一个浏览器标签中有一个繁忙的 up2k，<br>因此等待它完成",
		"ul_btnlk": "服务器配置已将此开关锁定到此状态",

		"udt_up": "上传",
		"udt_srch": "搜索",
		"udt_drop": "将文件拖放到这里",

		"u_nav_m": '<h6>好的，你有什么？</h6><code>Enter</code> = 文件（一个或多个）\n<code>ESC</code> = 一个文件夹（包括子文件夹）',
		"u_nav_b": '<a href="#" id="modal-ok">文件</a><a href="#" id="modal-ng">一个文件夹</a>',

		"cl_opts": "开关选项",
		"cl_themes": "主题",
		"cl_langs": "语言",
		"cl_ziptype": "文件夹下载",
		"cl_uopts": "up2k 开关",
		"cl_favico": "网站图标",
		"cl_bigdir": "最大目录数",
		"cl_hsort": "#sort", //m
		"cl_keytype": "键位符号",
		"cl_hiddenc": "隐藏列",
		"cl_hidec": "隐藏",
		"cl_reset": "重置",
		"cl_hpick": "点击列标题以在下表中隐藏",
		"cl_hcancel": "列隐藏已取消",

		"ct_grid": '网格视图',
		"ct_ttips": '◔ ◡ ◔">ℹ️ 工具提示',
		"ct_thumb": '在网格视图中，切换图标或缩略图$N快捷键: T">🖼️ 缩略图',
		"ct_csel": '在网格视图中使用 CTRL 和 SHIFT 进行文件选择">CTRL',
		"ct_ihop": '当图像查看器关闭时，滚动到最后查看的文件">滚动',
		"ct_dots": '显示隐藏文件（如果服务器允许）">隐藏文件',
		"ct_qdel": '删除文件时，只需确认一次">快删', //m
		"ct_dir1st": '在文件之前排序文件夹">📁 排序',
		"ct_nsort": '正确排序以数字开头的文件名">数字排序', //m
		"ct_utc": '所有时间请使用UTC">UTC', //m
		"ct_readme": '在文件夹列表中显示 README.md">📜 readme',
		"ct_idxh": '显示 index.html 代替文件夹列表">htm',
		"ct_sbars": '显示滚动条">⟊',

		"cut_umod": "如果文件已存在于服务器上，将服务器的最后修改时间戳更新为与你的本地文件匹配（需要写入和删除权限）\">re📅",

		"cut_turbo": "YOLO 按钮，你可能不想启用这个：$N$N如果你上传了大量文件并且由于某些原因需要重新启动，$N并且想要尽快继续上传，使用此选项$N$N这会用简单的 <em>&quot;服务器上的文件大小是否相同？&quot;</em> 替代哈希检查，$N因此如果文件内容不同，它将不会被上传$N$N上传完成后，你应该关闭此选项，$N然后重新&quot;上传&quot;相同的文件以让客户端验证它们\">加速",

		"cut_datechk": "除非启用「加速」按钮，否则没有效果$N$N略微减少 YOLO 因素；检查服务器上的文件时间戳是否与你的一致$N$N<em>理论上</em> 应该能捕捉到大多数未完成/损坏的上传，$N但不能替代之后禁用「加速」进行的验证\">日期检查",

		"cut_u2sz": "每个上传块的大小（以 MiB 为单位）；较大的值跨大西洋传输效果更好。在非常不可靠的连接上尝试较小的值",

		"cut_flag": "确保一次只有一个标签页在上传$N -- 其他标签页也必须启用此选项$N -- 仅影响同一域名下的标签页",

		"cut_az": "按字母顺序上传文件，而不是按最小文件优先$N$N按字母顺序可以更容易地查看服务器上是否出现了问题，但在光纤/局域网上传稍微慢一些",

		"cut_nag": "上传完成时的操作系统通知$N（仅当浏览器或标签页不活跃时）",
		"cut_sfx": "上传完成时的声音警报$N（仅当浏览器或标签页不活跃时）",

		"cut_mt": "使用多线程加速文件哈希$N$N这使用 Web Worker 并且需要更多内存（额外最多 512 MiB）$N$N这使得 https 快 30%，http 快 4.5 倍\">mt",

		"cut_wasm": "使用基于 WASM 的哈希计算器代替浏览器内置的哈希功能；这可以提升在基于 Chrome 的浏览器上的速度，但会增加 CPU 使用率，而且许多旧版本的 Chrome 存在漏洞，启用此功能会导致浏览器占用所有内存并崩溃。\">wasm", //m

		"cft_text": "网站图标文本（为空并刷新以禁用）",
		"cft_fg": "前景色",
		"cft_bg": "背景色",

		"cdt_lim": "文件夹中显示的最大文件数",
		"cdt_ask": "滚动到底部时，$N不会加载更多文件，$N而是询问你该怎么做",
		"cdt_hsort": "包含在媒体 URL 中的排序规则 (&lt;code&gt;,sorthref&lt;/code&gt;) 数量。将其设置为 0 时，点击媒体链接时也会忽略排序规则。", //m

		"tt_entree": "显示导航面板（目录树侧边栏）$N快捷键: B",
		"tt_detree": "显示面包屑导航$N快捷键: B",
		"tt_visdir": "滚动到选定的文件夹",
		"tt_ftree": "切换文件夹树 / 文本文件$N快捷键: V",
		"tt_pdock": "在顶部的停靠窗格中显示父文件夹",
		"tt_dynt": "随着树的展开自动增长",
		"tt_wrap": "自动换行",
		"tt_hover": "悬停时显示溢出的行$N（当鼠标光标在左侧边栏中时，滚动可能会中断）",

		"ml_pmode": "在文件夹末尾时...",
		"ml_btns": "命令",
		"ml_tcode": "转码",
		"ml_tcode2": "转换为", //m
		"ml_tint": "透明度",
		"ml_eq": "音频均衡器",
		"ml_drc": "动态范围压缩器",

		"mt_loop": "循环播放当前的歌曲\">🔁", //m
		"mt_one": "只播放一首歌后停止\">1️⃣", //m
		"mt_shuf": "在每个文件夹中随机播放歌曲\">🔀",
		"mt_aplay": "如果链接中有歌曲 ID，则自动播放,禁用此选项将停止在播放音乐时更新页面 URL 中的歌曲 ID，以防止在设置丢失但 URL 保留时自动播放\">自动播放▶",
		"mt_preload": "在歌曲快结束时开始加载下一首歌，以实现无缝播放\">预加载",
		"mt_prescan": "在最后一首歌结束之前切换到下一个文件夹$N保持网页浏览器活跃$N以免停止播放\">自动切换",
		"mt_fullpre": "尝试预加载整首歌；$N✅ 在 <b>不可靠</b> 连接上启用，$N❌ 可能在慢速连接上禁用\">加载整首歌",
		"mt_fau": "在手机上，如果下一首歌未能快速预加载，防止音乐停止（可能导致标签显示异常）\">☕️",
		"mt_waves": "波形进度条：$N显示音频幅度\">进度条",
		"mt_npclip": "显示当前播放歌曲的剪贴板按钮\">♪剪切板",
		"mt_m3u_c": "显示按钮以将所选歌曲$N复制为 m3u8 播放列表条目\">📻", //m
		"mt_octl": "操作系统集成（媒体快捷键 / OSD）\">OSD",
		"mt_oseek": "允许通过操作系统集成进行跳转$N$N注意：在某些设备（如 iPhone）上，$N这将替代下一首歌按钮\">seek",
		"mt_oscv": "在 OSD 中显示专辑封面\">封面",
		"mt_follow": "保持正在播放的曲目滚动到视图中\">🎯",
		"mt_compact": "紧凑的控制按钮\">⟎",
		"mt_uncache": "清除缓存&nbsp;$N（如果你的浏览器缓存了一个损坏的歌曲副本而拒绝播放，请尝试此操作）\">uncache",
		"mt_mloop": "循环打开的文件夹\">🔁 循环",
		"mt_mnext": "加载下一个文件夹并继续\">📂 下一首",
		"mt_mstop": "停止播放\">⏸ 停止", //m
		"mt_cflac": "将 flac / wav 转换为 {0}\">flac",
		"mt_caac": "将 aac / m4a 转换为 {0}\">aac",
		"mt_coth": "将所有其他（不是 mp3）转换为 {0}\">oth",
		"mt_c2opus": "适合桌面电脑、笔记本电脑和安卓设备的最佳选择\">opus", //m
		"mt_c2owa": "opus-weba（适用于 iOS 17.5 及更新版本）\">owa", //m
		"mt_c2caf": "opus-caf（适用于 iOS 11 到 iOS 17）\">caf", //m
		"mt_c2mp3": "适用于非常旧的设备\">mp3", //m
		"mt_c2flac": "最佳音质，但下载量很大\">flac", //m
		"mt_c2wav": "无压缩播放（更占空间）\">wav", //m
		"mt_c2ok": "不错的选择！", //m
		"mt_c2nd": "这不是您的设备推荐的输出格式，但应该没问题。", //m
		"mt_c2ng": "您的设备似乎不支持此输出格式，不过我们还是试试看吧。", //m
		"mt_xowa": "iOS 系统仍存在无法后台播放 owa 音乐的错误，请改用 caf 或 mp3 格式。", //m
		"mt_tint": "在进度条上设置背景级别（0-100）",
		"mt_eq": "启用均衡器和增益控制；$N$Nboost &lt;code&gt;0&lt;/code&gt; = 标准 100% 音量（默认）$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = 标准立体声（默认）$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% 左右交叉反馈$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = 单声道$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = 人声移除 )$N$N启用均衡器使无缝专辑完全无缝，所以如果你在乎这一点，请保持启用，所有值设为零（除了宽度 = 1）",
		"mt_drc": "启用动态范围压缩器（音量平滑器 / 限幅器）；还会启用均衡器以平衡音频，因此如果你不想要它，请将均衡器字段除了 '宽度' 外的所有字段设置为 0$N$N降低 THRESHOLD dB 以上的音频的音量；每超过 THRESHOLD dB 的 RATIO 会有 1 dB 输出，所以默认值 tresh -24 和 ratio 12 意味着它的音量不应超过 -22 dB，可以安全地将均衡器增益提高到 0.8，甚至在 ATK 0 和 RLS 如 90 的情况下提高到 1.8（仅在 Firefox 中有效；其他浏览器中 RLS 最大为 1）$N$N（见维基百科，他们解释得更好）",

		"mb_play": "播放",
		"mm_hashplay": "播放这个音频文件？",
		"mm_m3u": "按 <code>Enter/确定</code> 播放\n按 <code>ESC/取消</code> 编辑", //m
		"mp_breq": "需要 Firefox 82+ 或 Chrome 73+ 或 iOS 15+",
		"mm_bload": "正在加载...",
		"mm_bconv": "正在转换为 {0}，请稍等...",
		"mm_opusen": "你的浏览器无法播放 aac / m4a 文件；\n现在启用转码为 opus",
		"mm_playerr": "播放失败：",
		"mm_eabrt": "播放尝试已取消",
		"mm_enet": "你的互联网连接有问题",
		"mm_edec": "这个文件可能已损坏？？",
		"mm_esupp": "你的浏览器不支持这个音频格式",
		"mm_eunk": "未知错误",
		"mm_e404": "无法播放音频；错误 404：文件未找到。",
		"mm_e403": "无法播放音频；错误 403：访问被拒绝。\n\n尝试按 F5 重新加载，也许你已被注销",
		"mm_e500": "无法播放音频；错误 500：检查服务器日志。", //m
		"mm_e5xx": "无法播放音频；服务器错误",
		"mm_nof": "附近找不到更多音频文件",
		"mm_prescan": "正在寻找下一首音乐...",
		"mm_scank": "找到下一首歌：",
		"mm_uncache": "缓存已清除；所有歌曲将在下次播放时重新下载",
		"mm_hnf": "那首歌不再存在",

		"im_hnf": "那张图片不再存在",

		"f_empty": '该文件夹为空',
		"f_chide": '隐藏列 «{0}»\n\n你可以在设置选项卡中重新显示列',
		"f_bigtxt": "这个文件大小为 {0} MiB -- 真的以文本形式查看？",
		"f_bigtxt2": " 你想查看文件的结尾部分吗？这也将启用实时跟踪功能，能够实时显示新添加的文本行。", //m
		"fbd_more": '<div id="blazy">显示 <code>{0}</code> 个文件中的 <code>{1}</code> 个；<a href="#" id="bd_more">显示 {2}</a> 或 <a href="#" id="bd_all">显示全部</a></div>',
		"fbd_all": '<div id="blazy">显示 <code>{0}</code> 个文件中的 <code>{1}</code> 个；<a href="#" id="bd_all">显示全部</a></div>',
		"f_anota": "仅选择了 {0} 个项目，共 {1} 个；\n要选择整个文件夹，请先滚动到底部", //m

		"f_dls": '当前文件夹中的文件链接已\n更改为下载链接',

		"f_partial": "要安全下载正在上传的文件，请点击没有 <code>.PARTIAL</code> 文件扩展名的同名文件。请按取消或 Escape 执行此操作。\n\n按 确定 / Enter 将忽略此警告并继续下载 <code>.PARTIAL</code> 临时文件，这几乎肯定会导致数据损坏。",

		"ft_paste": "粘贴 {0} 项$N快捷键: ctrl-V",
		"fr_eperm": '无法重命名：\n你在此文件夹中没有 “移动” 权限',
		"fd_eperm": '无法删除：\n你在此文件夹中没有 “删除” 权限',
		"fc_eperm": '无法剪切：\n你在此文件夹中没有 “移动” 权限',
		"fp_eperm": '无法粘贴：\n你在此文件夹中没有 “写入” 权限',
		"fr_emore": "选择至少一个项目以重命名",
		"fd_emore": "选择至少一个项目以删除",
		"fc_emore": "选择至少一个项目以剪切",
		"fcp_emore": "选择至少一个要复制到剪贴板的项目", //m

		"fs_sc": "分享你所在的文件夹",
		"fs_ss": "分享选定的文件",
		"fs_just1d": "你不能同时选择多个文件夹，也不能同时选择文件夹和文件",
		"fs_abrt": "❌ 取消",
		"fs_rand": "🎲 随机名称",
		"fs_go": "✅ 创建分享",
		"fs_name": "名称",
		"fs_src": "源",
		"fs_pwd": "密码",
		"fs_exp": "过期",
		"fs_tmin": "分",
		"fs_thrs": "时",
		"fs_tdays": "天",
		"fs_never": "永久",
		"fs_pname": "链接名称可选；如果为空则随机",
		"fs_tsrc": "共享的文件或文件夹",
		"fs_ppwd": "密码可选",
		"fs_w8": "正在创建文件共享...",
		"fs_ok": "按 <code>Enter/确定</code> 复制到剪贴板\n按 <code>ESC/取消</code> 关闭",

		"frt_dec": "可能修复一些损坏的文件名\">url-decode",
		"frt_rst": "将修改后的文件名重置为原始文件名\">↺ 重置",
		"frt_abrt": "中止并关闭此窗口\">❌ 取消",
		"frb_apply": "应用重命名",
		"fr_adv": "批量 / 元数据 / 模式重命名\">高级",
		"fr_case": "区分大小写的正则表达式\">case",
		"fr_win": "Windows 安全名称；将 <code>&lt;&gt;:&quot;\\|?*</code> 替换为日文全角字符\">win",
		"fr_slash": "将 <code>/</code> 替换为不会导致新文件夹创建的字符\">不使用 /",
		"fr_re": "正则表达式搜索模式应用于原始文件名；$N可以在下面的格式字段中引用捕获组，如&lt;code&gt;(1)&lt;/code&gt;和&lt;code&gt;(2)&lt;/code&gt;等等。",
		"fr_fmt": "受到 foobar2000 的启发：$N&lt;code&gt;(title)&lt;/code&gt; 被歌曲名称替换,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; 仅当歌曲艺术家不为空时才包含&lt;code&gt;[此]&lt;/code&gt;部分$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; 将曲目编号填充为 2 位数字",
		"fr_pdel": "删除",
		"fr_pnew": "另存为",
		"fr_pname": "为你的新预设提供一个名称",
		"fr_aborted": "已中止",
		"fr_lold": "旧名称",
		"fr_lnew": "新名称",
		"fr_tags": "选定文件的标签（只读，仅供参考）：",
		"fr_busy": "正在重命名 {0} 项...\n\n{1}",
		"fr_efail": "重命名失败：\n",
		"fr_nchg": "{0} 个新名称由于 <code>win</code> 和/或 <code>不使用 /</code> 被更改\n\n确定继续使用这些更改的新名称？",

		"fd_ok": "删除成功",
		"fd_err": "删除失败：\n",
		"fd_none": "没有文件被删除；可能被服务器配置（xbd）阻止？",
		"fd_busy": "正在删除 {0} 项...\n\n{1}",
		"fd_warn1": "删除这 {0} 项？",
		"fd_warn2": "<b>最后机会！</b> 无法撤销。删除？",

		"fc_ok": "剪切 {0} 项",
		"fc_warn": '剪切 {0} 项\n\n但：只有 <b>这个</b> 浏览器标签页可以粘贴它们\n（因为选择非常庞大）',

		"fcc_ok": "已将 {0} 项复制到剪贴板", //m
		"fcc_warn": '已将 {0} 项复制到剪贴板\n\n但：只有 <b>这个</b> 浏览器标签页可以粘贴它们\n（因为选择非常庞大）', //m

		"fp_apply": "确认并立即粘贴", //m
		"fp_ecut": "首先剪切或复制一些文件/文件夹以粘贴/移动\n\n注意：你可以在不同的浏览器标签页之间剪切/粘贴", //m
		"fp_ename": "{0} 项不能移动到这里，因为名称已被占用。请在下方输入新名称以继续，或将名称留空以跳过这些项：", //m
		"fcp_ename": "{0} 项不能复制到这里，因为名称已被占用。请在下方输入新名称以继续，或将名称留空以跳过这些项：", //m
		"fp_emore": "还有一些文件名冲突需要解决", //m
		"fp_ok": "移动成功",
		"fcp_ok": "复制成功", //m
		"fp_busy": "正在移动 {0} 项...\n\n{1}",
		"fcp_busy": "正在复制 {0} 项...\n\n{1}", //m
		"fp_abrt": "正在中止...", //m
		"fp_err": "移动失败：\n",
		"fcp_err": "复制失败：\n", //m
		"fp_confirm": "将这些 {0} 项移动到这里？",
		"fcp_confirm": "将这些 {0} 项复制到这里？", //m
		"fp_etab": '无法从其他浏览器标签页读取剪贴板',
		"fp_name": "从你的设备上传一个文件。给它一个名字：",
		"fp_both_m": '<h6>选择粘贴内容</h6><code>Enter</code> = 从 «{1}» 移动 {0} 个文件\n<code>ESC</code> = 从你的设备上传 {2} 个文件',
		"fcp_both_m": '<h6>选择粘贴内容</h6><code>Enter</code> = 从 «{1}» 复制 {0} 个文件\n<code>ESC</code> = 从你的设备上传 {2} 个文件', //m
		"fp_both_b": '<a href="#" id="modal-ok">移动</a><a href="#" id="modal-ng">上传</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">复制</a><a href="#" id="modal-ng">上传</a>', //m

		"mk_noname": "在左侧文本框中输入名称，然后再执行此操作 :p",

		"tv_load": "加载文本文件：\n\n{0}\n\n{1}% ({2} 的 {3} MiB 已加载)",
		"tv_xe1": "无法加载文本文件：\n\n错误 ",
		"tv_xe2": "404，文件未找到",
		"tv_lst": "文本文件列表",
		"tvt_close": "返回到文件夹视图$N快捷键: M（或 Esc）\">❌ 关闭",
		"tvt_dl": "下载此文件$N快捷键: Y\">💾 下载",
		"tvt_prev": "显示上一个文档$N快捷键: i\">⬆ 上一个",
		"tvt_next": "显示下一个文档$N快捷键: K\">⬇ 下一个",
		"tvt_sel": "选择文件&nbsp;（用于剪切/删除/...）$N快捷键: S\">选择",
		"tvt_edit": "在文本编辑器中打开文件$N快捷键: E\">✏️ 编辑",
		"tvt_tail": "监视文件更改，并实时显示新增的行\">📡 跟踪", //m
		"tvt_wrap": "自动换行\">↵", //m
		"tvt_atail": "锁定到底部，显示最新内容\">⚓", //m
		"tvt_ctail": "解析终端颜色（ANSI 转义码）\">🌈", //m
		"tvt_ntail": "滚动历史上限（保留多少字节的文本）", //m

		"m3u_add1": "歌曲已添加到 m3u 播放列表", //m
		"m3u_addn": "已添加 {0} 首歌曲到 m3u 播放列表", //m
		"m3u_clip": "m3u 播放列表已复制到剪贴板\n\n请创建一个以 <code>.m3u</code> 结尾的文本文件，\n并将播放列表粘贴到该文件中；\n这样就可以播放了", //m

		"gt_vau": "不显示视频，仅播放音频\">🎧",
		"gt_msel": "启用文件选择；按住 ctrl 键点击文件以覆盖$N$N&lt;em&gt;当启用时：双击文件/文件夹以打开它&lt;/em&gt;$N$N快捷键：S\">多选",
		"gt_crop": "中心裁剪缩略图\">裁剪",
		"gt_3x": "高分辨率缩略图\">3x",
		"gt_zoom": "缩放",
		"gt_chop": "剪裁",
		"gt_sort": "排序依据",
		"gt_name": "名称",
		"gt_sz": "大小",
		"gt_ts": "日期",
		"gt_ext": "类型",
		"gt_c1": "截断文件名更多（显示更少）",
		"gt_c2": "截断文件名更少（显示更多）",

		"sm_w8": "正在搜索...",
		"sm_prev": "上次查询的搜索结果：\n  ",
		"sl_close": "关闭搜索结果",
		"sl_hits": "显示 {0} 个结果",
		"sl_moar": "加载更多",

		"s_sz": "大小",
		"s_dt": "日期",
		"s_rd": "路径",
		"s_fn": "名称",
		"s_ta": "标签",
		"s_ua": "上传于",
		"s_ad": "高级",
		"s_s1": "最小 MiB",
		"s_s2": "最大 MiB",
		"s_d1": "最早 iso8601",
		"s_d2": "最晚 iso8601",
		"s_u1": "上传后",
		"s_u2": "和/或之前",
		"s_r1": "路径包含 &nbsp;（空格分隔）",
		"s_f1": "名称包含 &nbsp;（用 -nope 否定）",
		"s_t1": "标签包含 &nbsp;（^=开头，$=结尾）",
		"s_a1": "特定元数据属性",

		"md_eshow": "无法渲染 ",
		"md_off": "[📜<em>readme</em>] 在 [⚙️] 中禁用 -- 文档隐藏",

		"badreply": "解析服务器回复失败",

		"xhr403": "403: 访问被拒绝\n\n尝试按 F5 可能会重新登录",
		"xhr0": "未知（可能丢失连接到服务器，或服务器离线）",
		"cf_ok": "抱歉 -- DD" + wah + "oS 保护启动\n\n事情应该在大约 30 秒后恢复\n\n如果没有任何变化，按 F5 重新加载页面",
		"tl_xe1": "无法列出子文件夹：\n\n错误 ",
		"tl_xe2": "404: 文件夹未找到",
		"fl_xe1": "无法列出文件夹中的文件：\n\n错误 ",
		"fl_xe2": "404: 文件夹未找到",
		"fd_xe1": "无法创建子文件夹：\n\n错误 ",
		"fd_xe2": "404: 父文件夹未找到",
		"fsm_xe1": "无法发送消息：\n\n错误 ",
		"fsm_xe2": "404: 父文件夹未找到",
		"fu_xe1": "无法从服务器加载未发布列表：\n\n错误 ",
		"fu_xe2": "404: 文件未找到??",

		"fz_tar": "未压缩的 gnu-tar 文件（linux / mac）",
		"fz_pax": "未压缩的 pax 格式 tar（较慢）",
		"fz_targz": "gnu-tar 带 gzip 级别 3 压缩$N$N通常非常慢，所以$N建议使用未压缩的 tar",
		"fz_tarxz": "gnu-tar 带 xz 级别 1 压缩$N$N通常非常慢，所以$N建议使用未压缩的 tar",
		"fz_zip8": "zip 带 utf8 文件名（在 windows 7 及更早版本上可能会出现问题）",
		"fz_zipd": "zip 带传统 cp437 文件名，适用于非常旧的软件",
		"fz_zipc": "cp437 带 crc32 提前计算，$N适用于 MS-DOS PKZIP v2.04g（1993 年 10 月）$N（处理时间较长，在下载开始之前）",

		"un_m1": "你可以删除下面的近期上传（或中止未完成的上传）",
		"un_upd": "刷新",
		"un_m4": "或分享下面可见的文件：",
		"un_ulist": "显示",
		"un_ucopy": "复制",
		"un_flt": "可选过滤器：&nbsp; URL 必须包含",
		"un_fclr": "清除过滤器",
		"un_derr": '未发布删除失败：\n',
		"un_f5": '出现问题，请尝试刷新或按 F5',
		"un_uf5": "抱歉，你必须刷新页面（例如，按 F5 或 CTRL-R），然后才能中止此上传",
		"un_nou": '<b>警告：</b> 服务器太忙，无法显示未完成的上传；稍后点击“刷新”链接',
		"un_noc": '<b>警告：</b> 服务器配置中未启用/允许完全上传文件的取消发布',
		"un_max": "显示前 2000 个文件（使用过滤器）",
		"un_avail": "{0} 个近期上传可以被删除<br />{1} 个未完成的上传可以被中止",
		"un_m2": "按上传时间排序；最新的在前：",
		"un_no1": "哎呀！没有足够新的上传",
		"un_no2": "哎呀！没有符合该过滤器的足够新的上传",
		"un_next": "删除下面的下一个 {0} 个文件",
		"un_abrt": "中止",
		"un_del": "删除",
		"un_m3": "正在加载你的近期上传...",
		"un_busy": "正在删除 {0} 个文件...",
		"un_clip": "{0} 个链接已复制到剪贴板",

		"u_https1": "你应该",
		"u_https2": "切换到 https",
		"u_https3": "以获得更好的性能",
		"u_ancient": '你的浏览器非常古老 -- 也许你应该 <a href="#" onclick="goto(\'bup\')">改用 bup</a>',
		"u_nowork": "需要 Firefox 53+ 或 Chrome 57+ 或 iOS 11+",
		"tail_2old": "需要 Firefox 105+ 或 Chrome 71+ 或 iOS 14.5+",
		"u_nodrop": '浏览器版本低，不支持通过拖动文件到窗口来上传文件',
		"u_notdir": "不是文件夹！\n\n您的浏览器太旧；\n请尝试将文件夹拖入窗口",
		"u_uri": "要从其他浏览器窗口拖放图片，\n请将其拖放到大的上传按钮上",
		"u_enpot": '切换到 <a href="#">简约 UI</a>（可能提高上传速度）',
		"u_depot": '切换到 <a href="#">精美 UI</a>（可能降低上传速度）',
		"u_gotpot": '切换到简化UI以提高上传速度，\n\n随时可以不同意并切换回去！',
		"u_pott": "<p>个文件： &nbsp; <b>{0}</b> 已完成， &nbsp; <b>{1}</b> 失败， &nbsp; <b>{2}</b> 正在处理， &nbsp; <b>{3}</b> 排队中</p>",
		"u_ever": "这是基本的上传工具； up2k 需要至少<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": '这是基本的上传工具；<a href="#" id="u2yea">up2k</a> 更好',
		"u_uput": '提高速度（跳过校验和）',
		"u_ewrite": '你对这个文件夹没有写入权限',
		"u_eread": '你对这个文件夹没有读取权限',
		"u_enoi": '文件搜索在服务器配置中未启用',
		"u_enoow": "无法覆盖此处的文件；需要删除权限", //m
		"u_badf": '这些 {0} 个文件（共 {1} 个）被跳过，可能是由于文件系统权限：\n\n',
		"u_blankf": '这些 {0} 个文件（共 {1} 个）是空白的；是否仍然上传？\n\n',
		"u_applef": "这些 {0} 个文件（共 {1} 个）可能是不需要的；\n按 <code>确定/Enter</code> 跳过以下文件，\n按 <code>取消/ESC</code> 取消排除，并上传这些文件：\n\n", //m
		"u_just1": '\n也许如果你只选择一个文件会更好',
		"u_ff_many": "如果你使用的是 <b>Linux / MacOS / Android，</b> 那么这个文件数量 <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>可能</em> 崩溃 Firefox!</a>\n如果发生这种情况，请再试一次（或使用 Chrome）。",
		"u_up_life": "此上传将在 {0} 后从服务器删除",
		"u_asku": '将这些 {0} 个文件上传到 <code>{1}</code>',
		"u_unpt": "你可以使用左上角的 🧯 撤销/删除此上传",
		"u_bigtab": '将显示 {0} 个文件,可能会导致您的浏览器崩溃。您确定吗？',
		"u_scan": '正在扫描文件...',
		"u_dirstuck": '您的浏览器无法访问以下 {0} 个文件/文件夹，它们将被跳过：',
		"u_etadone": '完成 ({0}, {1} 个文件)',
		"u_etaprep": '(准备上传)',
		"u_hashdone": '哈希完成',
		"u_hashing": '哈希',
		"u_hs": '正在等待服务器...',
		"u_started": "文件现在正在上传 🚀", //m
		"u_dupdefer": "这是一个重复文件。它将在所有其他文件上传后进行处理",
		"u_actx": "单击此文本以防止切换到其他窗口/选项卡时性能下降",
		"u_fixed": "好！&nbsp;已修复 👍",
		"u_cuerr": "上传块 {0} 的 {1} 失败；\n可能无害，继续中\n\n文件：{2}",
		"u_cuerr2": "服务器拒绝上传（块 {0} 的 {1}）；\n稍后重试\n\n文件：{2}\n\n错误 ",
		"u_ehstmp": "将重试；见右下角",
		"u_ehsfin": "服务器拒绝了最终上传请求；正在重试...",
		"u_ehssrch": "服务器拒绝了搜索请求；正在重试...",
		"u_ehsinit": "服务器拒绝了启动上传请求；正在重试...",
		"u_eneths": "进行上传握手时的网络错误；正在重试...",
		"u_enethd": "测试目标存在时的网络错误；正在重试...",
		"u_cbusy": "等待服务器在网络故障后再次信任我们...",
		"u_ehsdf": "服务器磁盘空间不足！\n\n将继续重试，以防有人\n释放足够的空间以继续",
		"u_emtleak1": "看起来你的网页浏览器可能有内存泄漏；\n请",
		"u_emtleak2": ' <a href="{0}">切换到 https（推荐）</a> 或 ',
		"u_emtleak3": ' ',
		"u_emtleakc": '尝试以下操作：\n<ul><li>按 <code>F5</code> 刷新页面</li><li>然后在&nbsp;<code>⚙️ 设置</code> 中禁用&nbsp;<code>mt</code>&nbsp;按钮</li><li>然后再次尝试上传</li></ul>上传会稍微慢一些，不过没关系。\n抱歉带来麻烦！\n\nPS：chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">已修复</a>此问题',
		"u_emtleakf": '尝试以下操作：\n<ul><li>按 <code>F5</code> 刷新页面</li><li>然后在上传 UI 中启用 <code>🥔</code>（土豆）<li>然后再次尝试上传</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">希望会在某个时点修复此问题</a>',
		"u_s404": "在服务器上未找到",
		"u_expl": "解释",
		"u_maxconn": "大多数浏览器限制为 6，但 Firefox 允许你通过 <code>connections-per-server</code> 在 <code>about:config</code> 中提高限制",
		"u_tu": '<p class="warn">警告：启用了 turbo，<span>&nbsp;客户端可能无法检测和恢复不完整的上传；查看 turbo 按钮工具提示</span></p>',
		"u_ts": '<p class="warn">警告：启用了 turbo，<span>&nbsp;搜索结果可能不正确；查看 turbo 按钮工具提示</span></p>',
		"u_turbo_c": "服务器配置中禁用了 turbo",
		"u_turbo_g": "禁用 turbo，因为你在此卷中没有\n目录列表权限",
		"u_life_cfg": '自动删除时间为 <input id="lifem" p="60" /> 分钟（或 <input id="lifeh" p="3600" /> 小时）',
		"u_life_est": '上传将在 <span id="lifew" tt="本地时间">---</span> 删除',
		"u_life_max": '此文件夹强制执行\n最大寿命为 {0}',
		"u_unp_ok": '允许取消发布 {0}',
		"u_unp_ng": '取消发布将不被允许',
		"ue_ro": '你对这个文件夹的访问是只读的\n\n',
		"ue_nl": '你当前未登录',
		"ue_la": '你当前以 "{0}" 登录',
		"ue_sr": '你当前处于文件搜索模式\n\n通过点击大搜索按钮旁边的放大镜 🔎 切换到上传模式，然后重试上传\n\n抱歉',
		"ue_ta": '尝试再次上传，现在应该能正常工作',
		"ue_ab": "这份文件正在上传到另一个文件夹，必须完成该上传后，才能将文件上传到其他位置。\n\n您可以通过左上角的🧯中止并忘记该上传。", //m
		"ur_1uo": "成功：文件上传成功",
		"ur_auo": "成功：所有 {0} 个文件上传成功",
		"ur_1so": "成功：文件在服务器上找到",
		"ur_aso": "成功：所有 {0} 个文件在服务器上找到",
		"ur_1un": "上传失败，抱歉",
		"ur_aun": "所有 {0} 个上传失败，抱歉",
		"ur_1sn": "文件未在服务器上找到",
		"ur_asn": "这些 {0} 个文件未在服务器上找到",
		"ur_um": "完成；\n{0} 个上传成功，\n{1} 个上传失败，抱歉",
		"ur_sm": "完成；\n{0} 个文件在服务器上找到，\n{1} 个文件未在服务器上找到",

		"lang_set": "刷新以使更改生效？",
	},
	"cze": {
		"tt": "Čeština",

		"cols": {
			"c": "tlačítka akcí",
			"dur": "doba trvání",
			"q": "kvalita / bitrate",
			"Ac": "audio kodek",
			"Vc": "video kodek",
			"Fmt": "formát / kontejner",
			"Ahash": "kontrolní součet audia",
			"Vhash": "kontrolní součet videa",
			"Res": "rozlišení",
			"T": "typ souboru",
			"aq": "kvalita zvuku / bitrate",
			"vq": "kvalita videa / bitrate",
			"pixfmt": "podvzorkování / struktura pixelů",
			"resw": "horizontální rozlišení",
			"resh": "vertikální rozlišení",
			"chs": "audio kanály",
			"hz": "vzorkovací frekvence"
		},

		"hks": [
			[
				"různé",
				["ESC", "zavřít různé věci"],

				"správce souborů",
				["G", "přepnout seznam / zobrazení mřížky"],
				["T", "přepnout náhledy / ikony"],
				["⇧ A/D", "velikost náhledů"],
				["ctrl-K", "smazat vybrané"],
				["ctrl-X", "vyjmout výběr do schránky"],
				["ctrl-C", "kopírovat výběr do schránky"],
				["ctrl-V", "vložit (přesunout/kopírovat) zde"],
				["Y", "stáhnout vybrané"],
				["F2", "přejmenovat vybrané"],

				"výběr souborů",
				["space", "přepnout výběr souboru"],
				["↑/↓", "posunout kurzor výběru"],
				["ctrl ↑/↓", "posunout kurzor a zobrazení"],
				["⇧ ↑/↓", "vybrat předchozí/následující soubor"],
				["ctrl-A", "vybrat všechny soubory / složky"],
			], [
				"navigace",
				["B", "přepnout drobečkovou navigaci / navigační panel"],
				["I/K", "předchozí/následující složka"],
				["M", "nadřazená složka (nebo sbalit aktuální)"],
				["V", "přepnout složky / textové soubory v navigačním panelu"],
				["A/D", "velikost navigačního panelu"],
			], [
				"audio přehrávač",
				["J/L", "předchozí/následující skladba"],
				["U/O", "přeskočit 10 sekund zpět/vpřed"],
				["0..9", "přejít na 0%..90%"],
				["P", "přehrát/pozastavit (také spustit)"],
				["S", "vybrat přehrávanou skladbu"],
				["Y", "stáhnout skladbu"],
			], [
				"prohlížeč obrázků",
				["J/L, ←/→", "předchozí/následující obrázek"],
				["Home/End", "první/poslední obrázek"],
				["F", "celá obrazovka"],
				["R", "otočit po směru hodinových ručiček"],
				["⇧ R", "otočit proti směru hodinových ručiček"],
				["S", "vybrat obrázek"],
				["Y", "stáhnout obrázek"],
			], [
				"video přehrávač",
				["U/O", "přeskočit 10 sekund zpět/vpřed"],
				["P/K/Space", "přehrát/pozastavit"],
				["C", "pokračovat přehráváním následující"],
				["V", "smyčka"],
				["M", "ztlumit"],
				["[ and ]", "nastavit interval smyčky"],
			], [
				"prohlížeč textových souborů",
				["I/K", "předchozí/následující soubor"],
				["M", "zavřít textový soubor"],
				["E", "upravit textový soubor"],
				["S", "vybrat soubor (pro vyjmutí/kopírování/přejmenování)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Zrušit",

		"enable": "Povolit",
		"danger": "NEBEZPEČÍ",
		"clipped": "zkopírováno do schránky",

		"ht_s1": "sekunda",
		"ht_s2": "sekundy",
		"ht_s5": "sekund",
		"ht_m1": "minuta",
		"ht_m2": "minuty",
		"ht_m5": "minut",
		"ht_h1": "hodina",
		"ht_h2": "hodiny",
		"ht_h5": "hodin",
		"ht_d1": "den",
		"ht_d2": "dny",
		"ht_d5": "dní",
		"ht_and": " a ",

		"goh": "ovládací panel",
		"gop": 'předchozí sourozenec">předchozí',
		"gou": 'nadřazená složka">nahoru',
		"gon": 'následující složka">následující',
		"logout": "Odhlásit ",
		"login": "Přihlásit se", //m
		"access": " přístup",
		"ot_close": "zavřít podnabídku",
		"ot_search": "hledat soubory podle atributů, cesty / názvu, hudebních tagů nebo jejich kombinace$N$N&lt;code&gt;foo bar&lt;/code&gt; = musí obsahovat jak «foo» tak «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = musí obsahovat «foo» ale ne «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = začíná na «yana» a je to «opus» soubor$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = obsahuje přesně «try unite»$N$Nformát data je iso-8601, jako$N&lt;code&gt;2009-12-31&lt;/code&gt; nebo &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: smazat vaše nedávné nahrání nebo zrušit nedokončené",
		"ot_bup": "bup: základní nahrávač, podporuje i netscape 4.0",
		"ot_mkdir": "mkdir: vytvořit nový adresář",
		"ot_md": "new-md: vytvořit nový markdown dokument",
		"ot_msg": "msg: poslat zprávu do logu serveru",
		"ot_mp": "možnosti přehrávače médií",
		"ot_cfg": "možnosti konfigurace",
		"ot_u2i": 'up2k: nahrát soubory (pokud máte oprávnění k zápisu) nebo přepnout do vyhledávacího režimu a podívat se, zda existují někde na serveru$N$Nnahrávání je obnovitelné, vícevláknové a časové značky souborů jsou zachovány, ale používá více CPU než [🎈]&nbsp; (základní nahrávač)<br /><br />během nahrávání se tato ikona stává indikátorem průběhu!',
		"ot_u2w": 'up2k: nahrát soubory s podporou obnovení (zavřete prohlížeč a stejné soubory přetáhněte později)$N$Nvícevláknové a časové značky souborů jsou zachovány, ale používá více CPU než [🎈]&nbsp; (základní nahrávač)<br /><br />během nahrávání se tato ikona stává indikátorem průběhu!',
		"ot_noie": 'Prosím použijte Chrome / Firefox / Edge',

		"ab_mkdir": "vytvořit adresář",
		"ab_mkdoc": "nový markdown dokument",
		"ab_msg": "poslat zprávu do logu serveru",

		"ay_path": "přejít na složky",
		"ay_files": "přejít na soubory",

		"wt_ren": "přejmenovat vybrané položky$NKlávesová zkratka: F2",
		"wt_del": "smazat vybrané položky$NKlávesová zkratka: ctrl-K",
		"wt_cut": "vyjmout vybrané položky &lt;small&gt;(pak je vložit někam jinam)&lt;/small&gt;$NKlávesová zkratka: ctrl-X",
		"wt_cpy": "kopírovat vybrané položky do schránky$N(pro vložení někam jinam)$NKlávesová zkratka: ctrl-C",
		"wt_pst": "vložit dříve vyjmutý / zkopírovaný výběr$NKlávesová zkratka: ctrl-V",
		"wt_selall": "vybrat všechny soubory$NKlávesová zkratka: ctrl-A (když je zaměřen soubor)",
		"wt_selinv": "invertovat výběr",
		"wt_zip1": "stáhnout tuto složku jako archiv",
		"wt_selzip": "stáhnout výběr jako archiv",
		"wt_seldl": "stáhnout výběr jako samostatné soubory$NKlávesová zkratka: Y",
		"wt_npirc": "kopírovat informace o stopě ve formátu irc",
		"wt_nptxt": "kopírovat informace o stopě v prostém textu",
		"wt_m3ua": "přidat do m3u playlistu (klikněte později na <code>📻kopírovat</code>)",
		"wt_m3uc": "kopírovat m3u playlist do schránky",
		"wt_grid": "přepnout zobrazení mřížky / seznamu$NKlávesová zkratka: G",
		"wt_prev": "předchozí stopa$NKlávesová zkratka: J",
		"wt_play": "přehrát / pozastavit$NKlávesová zkratka: P",
		"wt_next": "následující stopa$NKlávesová zkratka: L",

		"ul_par": "paralelní nahrávání:",
		"ut_rand": "náhodné názvy souborů",
		"ut_u2ts": "kopírovat časovou značku poslední změny$Nz vašeho souborového systému na server\">📅",
		"ut_ow": "přepsat existující soubory na serveru?$N🛡️: nikdy (místo toho vytvoří nový název souboru)$N🕒: přepsat pokud je soubor na serveru starší než váš$N♻️: vždy přepsat pokud se soubory liší",
		"ut_mt": "pokračovat v hashování ostatních souborů během nahrávání$N$Nmožná zakázat pokud je vaše CPU nebo HDD bottleneckem",
		"ut_ask": 'požádat o potvrzení před zahájením nahrávání">💭',
		"ut_pot": "zlepšit rychlost nahrávání na pomalých zařízeních$Nzjednodušením UI",
		"ut_srch": "skutečně nenahrávat, místo toho zkontrolovat zda soubory již $N existují na serveru (prohledá všechny složky které můžete číst)",
		"ut_par": "pozastavit nahrávání nastavením na 0$N$Nzvýšit pokud je vaše připojení pomalé / vysoká latence$N$Nponechat na 1 v LAN nebo pokud je HDD serveru bottleneckem",
		"ul_btn": "přetáhněte soubory / složky<br>sem (nebo sem klikněte)",
		"ul_btnu": "N A H R Á T",
		"ul_btns": "H L E D A T",

		"ul_hash": "hash",
		"ul_send": "odeslat",
		"ul_done": "hotovo",
		"ul_idle1": "zatím nejsou zařazena žádná nahrávání",
		"ut_etah": "průměrná rychlost &lt;em&gt;hashování&lt;/em&gt; a odhadovaný čas do dokončení",
		"ut_etau": "průměrná rychlost &lt;em&gt;nahrávání&lt;/em&gt; a odhadovaný čas do dokončení",
		"ut_etat": "průměrná &lt;em&gt;celková&lt;/em&gt; rychlost a odhadovaný čas do dokončení",

		"uct_ok": "úspěšně dokončeno",
		"uct_ng": "nedobré: selhalo / odmítnuto / nenalezeno",
		"uct_done": "celkem",
		"uct_bz": "hashování nebo nahrávání",
		"uct_q": "nečinné, čekající",

		"utl_name": "název souboru",
		"utl_ulist": "seznam",
		"utl_ucopy": "kopírovat",
		"utl_links": "odkazy",
		"utl_stat": "stav",
		"utl_prog": "průběh",

		// keep short:
		"utl_404": "404",
		"utl_err": "CHYBA",
		"utl_oserr": "chyba OS",
		"utl_found": "nalezeno",
		"utl_defer": "odložit",
		"utl_yolo": "YOLO",
		"utl_done": "hotovo",

		"ul_flagblk": "soubory byly přidány do fronty</b><br>nicméně v jiné kartě prohlížeče běží up2k,<br>takže čekáme až skončí",
		"ul_btnlk": "konfigurace serveru uzamkla tento přepínač v tomto stavu",

		"udt_up": "Nahrávání",
		"udt_srch": "Hledání",
		"udt_drop": "přetáhněte to sem",

		"u_nav_m": '<h6>jasnačka, co máte?</h6><code>Enter</code> = Soubory (jeden nebo více)\n<code>ESC</code> = Jednu složku (včetně podsložek)',
		"u_nav_b": '<a href="#" id="modal-ok">Soubory</a><a href="#" id="modal-ng">Jedna složka</a>',

		"cl_opts": "přepínače",
		"cl_themes": "téma",
		"cl_langs": "jazyk",
		"cl_ziptype": "stahování složky",
		"cl_uopts": "up2k přepínače",
		"cl_favico": "favicon",
		"cl_bigdir": "velké adresáře",
		"cl_hsort": "#řazení",
		"cl_keytype": "notace kláves",
		"cl_hiddenc": "skryté sloupce",
		"cl_hidec": "skrýt",
		"cl_reset": "resetovat",
		"cl_hpick": "klepněte na záhlaví sloupců pro skrytí v tabulce níže",
		"cl_hcancel": "skrývání sloupců zrušeno",

		"ct_grid": '田 mřížka',
		"ct_ttips": '◔ ◡ ◔">ℹ️ nápovědy',
		"ct_thumb": 'v zobrazení mřížky přepnout ikony nebo náhledy$NKlávesová zkratka: T">🖼️ náhledy',
		"ct_csel": 'použít CTRL a SHIFT pro výběr souborů v zobrazení mřížky">výběr',
		"ct_ihop": 'když se zavře prohlížeč obrázků, posunout dolů k naposledy zobrazenému souboru">g⮯',
		"ct_dots": 'zobrazit skryté soubory (pokud to server povoluje)">dotfiles',
		"ct_qdel": 'při mazání souborů požádat o potvrzení jen jednou">rychlé mazání',
		"ct_dir1st": 'řadit složky před soubory">📁 první',
		"ct_nsort": 'přirozené řazení (pro názvy souborů s úvodními číslicemi)">přirozené řazení',
		"ct_utc": 'zobrazit všechny časy v UTC">UTC',
		"ct_readme": 'zobrazit README.md v seznamech složek">📜 readme',
		"ct_idxh": 'zobrazit index.html místo seznamu složky">htm',
		"ct_sbars": 'zobrazit posuvníky">⟊',

		"cut_umod": "pokud soubor na serveru již existuje, aktualizovat časovou značku posledního změny serveru tak, aby odpovídala vašemu lokálnímu souboru (vyžaduje oprávnění k zápisu+mazání)\">re📅",

		"cut_turbo": "yolo tlačítko, pravděpodobně to NECHCETE povolit:$N$Npoužijte to pokud jste nahrávali obrovské množství souborů a museli jste restartovat z nějakého důvodu a chcete pokračovat v nahrávání ASAP$N$Ntoto nahradí hash-kontrolu jednoduchým <em>&quot;má to stejnou velikost souboru na serveru?&quot;</em> takže pokud se obsah souborů liší, NEBUDE nahrán$N$Nměli byste to vypnout když nahrávání skončí a pak znovu &quot;nahrát&quot; stejné soubory aby je klient ověřil\">turbo",

		"cut_datechk": "nemá žádný efekt pokud není povoleno turbo tlačítko$N$Nsnižuje yolo faktor o trochu; kontroluje zda časové značky souborů na serveru odpovídají vašim$N$Nměl by <em>teoreticky</em> zachytit většinu nedokončených / poškozených nahrávání, ale není náhradou za ověřovací průchod s turbem vypnutým poté\">kontrola data",

		"cut_u2sz": "velikost (v MiB) každého kusu nahrávání; velké hodnoty lépe létají přes atlantik. Zkuste nízké hodnoty na velmi nespolehlivých připojeních",

		"cut_flag": "zajistit aby nahrávala jen jedna karta najednou $N -- ostatní karty to musí mít také povoleno $N -- ovlivňuje jen karty na stejné doméně",

		"cut_az": "nahrávat soubory v abecedním pořadí, spíše než nejmenší-soubor-první$N$Nabecední pořadí může usnadnit kontrolu zda se něco pokazilo na serveru, ale činí nahrávání mírně pomalejší na optice / LAN",

		"cut_nag": "notifikace OS když nahrávání skončí$N(jen pokud prohlížeč nebo karta není aktivní)",
		"cut_sfx": "zvukové upozornění když nahrávání skončí$N(jen pokud prohlížeč nebo karta není aktivní)",

		"cut_mt": "použít vícevláknové zpracování pro zrychlení hashování souborů$N$Ntoto používá web-workers a vyžaduje$Nvíce RAM (až 512 MiB navíc)$N$Ndělá https o 30% rychlejší a http 4,5x rychlejší\">mt",

		"cut_wasm": "použijte wasm místo vestavěného hashování prohlížeče; zlepšuje rychlost na prohlížečích založených na chrome ale zvyšuje zátěž CPU, mnoho starších verzí chrome má chyby které způsobují že prohlížeč spotřebuje veškerou RAM a spadne pokud je toto povoleno\">wasm",

		"cft_text": "text favicon (prázdné a obnovte pro zakázání)",
		"cft_fg": "barva popředí",
		"cft_bg": "barva pozadí",

		"cdt_lim": "maximální počet souborů k zobrazení ve složce",
		"cdt_ask": "při posunování na konec,$Nmísto načítání více souborů,$N se zeptat co dělat",
		"cdt_hsort": "kolik pravidel řazení (&lt;code&gt;,sorthref&lt;/code&gt;) zahrnout do media-URL. Nastavení na 0 bude také ignorovat pravidla řazení zahrnutá v media odkazech při kliknutí na ně",

		"tt_entree": "zobrazit navigační panel (postranní strom adresářů)$NKlávesová zkratka: B",
		"tt_detree": "zobrazit drobečkovou navigaci$NKlávesová zkratka: B",
		"tt_visdir": "posunout k vybrané složce",
		"tt_ftree": "přepnout strom složek / textové soubory$NKlávesová zkratka: V",
		"tt_pdock": "zobrazit nadřazené složky v ukotveném panelu nahoře",
		"tt_dynt": "automaticky rozrůstat jak se strom rozšiřuje",
		"tt_wrap": "zalomení řádků",
		"tt_hover": "odhalit přetékající řádky při najetí$N( ruší posun pokud kurzor myši $N&nbsp; není v levém okraji )",

		"ml_pmode": "na konci složky...",
		"ml_btns": "příkazy",
		"ml_tcode": "transkódovat",
		"ml_tcode2": "transkódovat na",
		"ml_tint": "odstín",
		"ml_eq": "audio ekvalizér",
		"ml_drc": "kompresor dynamického rozsahu",

		"mt_loop": "smyčka/opakovat jednu skladbu\">🔁",
		"mt_one": "zastavit po jedné skladbě\">1️⃣",
		"mt_shuf": "zamíchat skladby v každé složce\">🔀",
		"mt_aplay": "automatické přehrávání pokud je ID skladby v odkazu kterým jste přišli na server$N$Nzakázání toho také zastaví aktualizaci URL stránky s ID skladby při přehrávání hudby, aby se zabránilo automatickému přehrávání pokud se tato nastavení ztratí ale URL zůstane\">a▶",
		"mt_preload": "začít načítat následující skladbu před koncem pro plynulé přehrávání\">přednahrání",
		"mt_prescan": "přejít do následující složky před tím než$Nskončí poslední skladba, aby byl webprohlížeč$Nspokojen aby nezastavil přehrávání\">nav",
		"mt_fullpre": "zkusit přednahrát celou skladbu;$N✅ povolit na <b>nespolehlivých</b> připojeních,$N❌ <b>zakázat</b> na pomalých připojeních pravděpodobně\">úplné",
		"mt_fau": "na telefonech zabránit zastavení hudby, pokud se další píseň nenahraje dostatečně rychle (může způsobit chybné zobrazení tagů)\">☕️",
		"mt_waves": "vlnový posuvník:$Nzobrazit amplitudu zvuku v posuvníku\">~s",
		"mt_npclip": "zobrazit tlačítka pro kopírování aktuálně přehrávané písně do schránky\">/np",
		"mt_m3u_c": "zobrazit tlačítka pro kopírování$Nvybraných písní jako položky m3u8 playlistu\">📻",
		"mt_octl": "integrace s OS (mediální klávesy / osd)\">os-ctl",
		"mt_oseek": "povolit posunování přes integraci s OS$N$Npoznámka: na některých zařízeních (iPhone),$Nto nahradí tlačítko další písně\">seek",
		"mt_oscv": "zobrazit obal alba v osd\">art",
		"mt_follow": "udržet přehrávanou stopu v zobrazení\">🎯",
		"mt_compact": "kompaktní ovládání\">⟎",
		"mt_uncache": "vymazat cache &nbsp;(zkuste to, pokud váš prohlížeč uložil$Nporušenou kopii písně a odmítá ji přehrát)\">uncache",
		"mt_mloop": "opakovat otevřenou složku\">🔁 loop",
		"mt_mnext": "načíst další složku a pokračovat\">📂 next",
		"mt_mstop": "zastavit přehrávání\">⏸ stop",
		"mt_cflac": "převést flac / wav na {0}\">flac",
		"mt_caac": "převést aac / m4a na {0}\">aac",
		"mt_coth": "převést všechny ostatní (ne mp3) na {0}\">oth",
		"mt_c2opus": "nejlepší volba pro desktopy, laptopy, android\">opus",
		"mt_c2owa": "opus-weba, pro iOS 17.5 a novější\">owa",
		"mt_c2caf": "opus-caf, pro iOS 11 až 17\">caf",
		"mt_c2mp3": "použijte na velmi starých zařízeních\">mp3",
		"mt_c2flac": "nejlepší kvalita zvuku, ale obrovské stahování\">flac",
		"mt_c2wav": "nekomprimované přehrávání (ještě větší)\">wav",
		"mt_c2ok": "výborně, dobrá volba",
		"mt_c2nd": "to není doporučený výstupní formát pro vaše zařízení, ale v pořádku",
		"mt_c2ng": "vaše zařízení, zdá se, nepodporuje tento výstupní formát, ale zkusíme to",
		"mt_xowa": "v iOS jsou chyby bránící přehrávání na pozadí s tímto formátem; použijte prosím caf nebo mp3",
		"mt_tint": "úroveň pozadí (0-100) na posuvníku$Nabyste učinili ukládání do vyrovnávací paměti méně rušivým",
		"mt_eq": "povoluje ekvalizér a ovládání zisku;$N$Nboost &lt;code&gt;0&lt;/code&gt; = standardní 100% hlasitost (nezměněno)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = standardní stereo (nezměněno)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% levý-pravý crossfeed$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = odstranění vokálů :^)$N$Npovolení ekvalizéru činí alba bez mezer zcela bez mezer, takže to nechte zapnuté se všemi hodnotami na nule (kromě width = 1), pokud vám na tom záleží",
		"mt_drc": "povoluje kompresor dynamického rozsahu (vyrovnávač hlasitosti / brickwaller); také povolí EQ pro vyvážení špaget, takže nastavte všechna EQ pole kromě 'width' na 0, pokud to nechcete$N$Nsnižuje hlasitost zvuku nad THRESHOLD dB; pro každý RATIO dB za THRESHOLD je 1 dB výstupu, takže výchozí hodnoty tresh -24 a ratio 12 znamenají, že by nikdy nemělo být hlasitější než -22 dB a je bezpečné zvýšit boost ekvalizéru na 0.8, nebo dokonce 1.8 s ATK 0 a obrovským RLS jako 90 (funguje pouze ve firefoxu; RLS je max 1 v jiných prohlížečích)$N$N(viz wikipedia, vysvětlují to mnohem lépe)",

		"mb_play": "přehrát",
		"mm_hashplay": "přehrát tento audio soubor?",
		"mm_m3u": "stiskněte <code>Enter/OK</code> pro Přehrání\nstiskněte <code>ESC/Zrušit</code> pro Úpravu",
		"mp_breq": "potřebujete firefox 82+ nebo chrome 73+ nebo iOS 15+",
		"mm_bload": "nyní se načítá...",
		"mm_bconv": "převádí se na {0}, čekejte prosím...",
		"mm_opusen": "váš prohlížeč nemůže přehrát aac / m4a soubory;\ntranscoding na opus je nyní povolen",
		"mm_playerr": "přehrávání selhalo: ",
		"mm_eabrt": "Pokus o přehrávání byl zrušen",
		"mm_enet": "Vaše internetové připojení je nestabilní",
		"mm_edec": "Tento soubor je údajně poškozený??",
		"mm_esupp": "Váš prohlížeč nerozumí tomuto audio formátu",
		"mm_eunk": "Neznámá chyba",
		"mm_e404": "Nelze přehrát audio; chyba 404: Soubor nenalezen.",
		"mm_e403": "Nelze přehrát audio; chyba 403: Přístup odepřen.\n\nZkuste stisknout F5 pro obnovení, možná jste se odhlásili",
		"mm_e500": "Nelze přehrát audio; chyba 500: Zkontrolujte logy serveru.",
		"mm_e5xx": "Nelze přehrát audio; chyba serveru ",
		"mm_nof": "žádné další audio soubory v okolí nenalezeny",
		"mm_prescan": "Hledám hudbu k dalšímu přehrání...",
		"mm_scank": "Další píseň nalezena:",
		"mm_uncache": "cache vymazána; všechny písně se znovu stáhnou při dalším přehrávání",
		"mm_hnf": "tato píseň již neexistuje",

		"im_hnf": "tento obrázek již neexistuje",

		"f_empty": 'tato složka je prázdná',
		"f_chide": 'toto skryje sloupec «{0}»\n\nmůžete odkrýt sloupce v záložce nastavení',
		"f_bigtxt": "tento soubor má {0} MiB -- opravdu zobrazit jako text?",
		"f_bigtxt2": "zobrazit pouze konec souboru? to také povolí sledování/tailing, zobrazí nově přidané řádky textu v reálném čase",
		"fbd_more": '<div id="blazy">zobrazuji <code>{0}</code> z <code>{1}</code> souborů; <a href="#" id="bd_more">zobraz {2}</a> nebo <a href="#" id="bd_all">zobraz všechny</a></div>',
		"fbd_all": '<div id="blazy">zobrazuji <code>{0}</code> z <code>{1}</code> souborů; <a href="#" id="bd_all">zobraz všechny</a></div>',
		"f_anota": "pouze {0} z {1} položek bylo vybráno;\npro výběr celé složky nejprve přejděte na konec",

		"f_dls": 'odkazy na soubory v aktuální složce byly\nzměněny na odkazy ke stažení',

		"f_partial": "Pro bezpečné stažení souboru, který se aktuálně nahrává, klikněte prosím na soubor se stejným názvem, ale bez přípony <code>.PARTIAL</code>. Stiskněte prosím Zrušit nebo Escape.\n\nStisknutím OK / Enter ignorujete toto varování a pokračujete ve stahování <code>.PARTIAL</code> dočasného souboru, což téměř jistě vyústí jako poškozená data.",

		"ft_paste": "vložit {0} položek$NKlávesová zkratka: ctrl-V",
		"fr_eperm": 'nelze přejmenovat:\nnemáte oprávnění “přesunout” v této složce',
		"fd_eperm": 'nelze smazat:\nnemáte oprávnění “smazat” v této složce',
		"fc_eperm": 'nelze vyjmout:\nnemáte oprávnění “přesunout” v této složce',
		"fp_eperm": 'nelze vložit:\nnemáte oprávnění “zapisovat” v této složce',
		"fr_emore": "vyberte alespoň jednu položku k přejmenování",
		"fd_emore": "vyberte alespoň jednu položku ke smazání",
		"fc_emore": "vyberte alespoň jednu položku k vyjmutí",
		"fcp_emore": "vyberte alespoň jednu položku k zkopírování do schránky",

		"fs_sc": "sdílet složku, ve které se nacházíte",
		"fs_ss": "sdílet vybrané soubory",
		"fs_just1d": "nelze vybrat více než jednu složku,\nnebo míchat soubory a složky v jednom výběru",
		"fs_abrt": "❌ zrušit",
		"fs_rand": "🎲 náhodný.název",
		"fs_go": "✅ vytvořit sdílení",
		"fs_name": "název",
		"fs_src": "zdroj",
		"fs_pwd": "heslo",
		"fs_exp": "vypršení",
		"fs_tmin": "min",
		"fs_thrs": "hodin",
		"fs_tdays": "dní",
		"fs_never": "navždy",
		"fs_pname": "volitelný název odkazu; bude náhodný, pokud je prázdný",
		"fs_tsrc": "soubor nebo složka ke sdílení",
		"fs_ppwd": "volitelné heslo",
		"fs_w8": "vytváření sdílení...",
		"fs_ok": "stiskněte <code>Enter/OK</code> pro zkopírování do schránky\nstiskněte <code>ESC/Zrušit</code> pro zavření",

		"frt_dec": "může opravit některé případy porušených názvů souborů\">url-decode",
		"frt_rst": "resetovat změněné názvy souborů zpět na původní\">↺ reset",
		"frt_abrt": "zrušit a zavřít toto okno\">❌ cancel",
		"frb_apply": "PŘEJMENOVAT",
		"fr_adv": "dávkové / metadata / přejmenování podle vzoru\">pokročilé",
		"fr_case": "regex citlivý na velikost písmen\">velikost",
		"fr_win": "názvy bezpečné pro windows; nahradit <code>&lt;&gt;:&quot;\\|?*</code> japonskými plnošířkovými znaky\">win",
		"fr_slash": "nahradit <code>/</code> znakem který nezpůsobí vytvoření nových složek\">žádné /",
		"fr_re": "vzor regex hledání k aplikaci na původní názvy souborů; zachycené skupiny mohou být odkazovány v poli formátu níže jako &lt;code&gt;(1)&lt;/code&gt; a &lt;code&gt;(2)&lt;/code&gt; atd.",
		"fr_fmt": "inspirováno foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; je nahrazeno názvem skladby,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; přeskočí [tuto] část pokud je umělec prázdný$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; doplní číslo stopy na 2 číslice",
		"fr_pdel": "smazat",
		"fr_pnew": "uložit jako",
		"fr_pname": "zadejte název pro vaše nové přednastavení",
		"fr_aborted": "zrušeno",
		"fr_lold": "starý název",
		"fr_lnew": "nový název",
		"fr_tags": "tagy pro vybrané soubory (pouze pro čtení, jen pro referenci):",
		"fr_busy": "přejmenovávám {0} položek...\n\n{1}",
		"fr_efail": "přejmenování selhalo:\n",
		"fr_nchg": "{0} z nových názvů bylo změněno kvůli <code>win</code> a/nebo <code>žádné /</code>\n\nPokračovat s těmito změněnými novými názvy?",

		"fd_ok": "mazání OK",
		"fd_err": "mazání selhalo:\n",
		"fd_none": "nic nebylo smazáno; možná blokováno konfigurací serveru (xbd)?",
		"fd_busy": "mažu {0} položek...\n\n{1}",
		"fd_warn1": "SMAZAT těchto {0} položek?",
		"fd_warn2": "<b>Poslední šance!</b> Nelze vrátit zpět. Smazat?",

		"fc_ok": "vyjmout {0} položek",
		"fc_warn": 'vyjmout {0} položek\n\nale: pouze <b>tato</b> karta prohlížeče je může vložit\n(protože výběr je tak absolutně masivní)',

		"fcc_ok": "zkopírováno {0} položek do schránky",
		"fcc_warn": 'zkopírováno {0} položek do schránky\n\nale: pouze <b>tato</b> karta prohlížeče je může vložit\n(protože výběr je tak absolutně masivní)',

		"fp_apply": "použít tyto názvy",
		"fp_ecut": "nejprve vyjměte nebo zkopírujte nějaké soubory / složky k vložení / přesunutí\n\npoznámka: můžete vyjmout / vložit přes různé karty prohlížeče",
		"fp_ename": "{0} položek sem nelze přesunout protože názvy jsou již obsazené. Dejte jim nové názvy níže pro pokračování, nebo název nechte prázdný pro přeskočení:",
		"fcp_ename": "{0} položek sem nelze zkopírovat protože názvy jsou již obsazené. Dejte jim nové názvy níže pro pokračování, nebo název nechte prázdný pro přeskočení:",
		"fp_emore": "stále jsou některé kolize názvů souborů k opravě",
		"fp_ok": "přesun OK",
		"fcp_ok": "kopírování OK",
		"fp_busy": "přesouvám {0} položek...\n\n{1}",
		"fcp_busy": "kopíruji {0} položek...\n\n{1}",
		"fp_abrt": "přerušuji...", //m
		"fp_err": "přesun selhal:\n",
		"fcp_err": "kopírování selhalo:\n",
		"fp_confirm": "přesunout těchto {0} položek sem?",
		"fcp_confirm": "zkopírovat těchto {0} položek sem?",
		"fp_etab": 'selhalo čtení schránky z jiné karty prohlížeče',
		"fp_name": "nahrávání souboru z vašeho zařízení. Dejte mu název:",
		"fp_both_m": '<h6>vyberte co vložit</h6><code>Enter</code> = Přesunout {0} souborů z «{1}»\n<code>ESC</code> = Nahrát {2} souborů z vašeho zařízení',
		"fcp_both_m": '<h6>vyberte co vložit</h6><code>Enter</code> = Kopírovat {0} souborů z «{1}»\n<code>ESC</code> = Nahrát {2} souborů z vašeho zařízení',
		"fp_both_b": '<a href="#" id="modal-ok">Přesunout</a><a href="#" id="modal-ng">Nahrát</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopírovat</a><a href="#" id="modal-ng">Nahrát</a>',

		"mk_noname": "napište název do textového pole vlevo předtím než to uděláte :p",

		"tv_load": "Načítání textového dokumentu:\n\n{0}\n\n{1}% ({2} z {3} MiB načteno)",
		"tv_xe1": "nelze načíst textový soubor:\n\nchyba ",
		"tv_xe2": "404, soubor nenalezen",
		"tv_lst": "seznam textových souborů v",
		"tvt_close": "návrat do zobrazení složky$NKlávesová zkratka: M (nebo Esc)\">❌ zavřít",
		"tvt_dl": "stáhnout tento soubor$NKlávesová zkratka: Y\">💾 stáhnout",
		"tvt_prev": "zobrazit předchozí dokument$NKlávesová zkratka: i\">⬆ předchozí",
		"tvt_next": "zobrazit následující dokument$NKlávesová zkratka: K\">⬇ další",
		"tvt_sel": "vybrat soubor &nbsp; ( pro vyjmutí / kopírování / mazání / ... )$NKlávesová zkratka: S\">výběr",
		"tvt_edit": "otevřít soubor v textovém editoru$NKlávesová zkratka: E\">✏️ upravit",
		"tvt_tail": "sledovat soubor pro změny; zobrazit nové řádky v reálném čase\">📡 sledovat",
		"tvt_wrap": "zalamování slov\">↵",
		"tvt_atail": "zamknout posun na konec stránky\">⚓",
		"tvt_ctail": "dekódovat barvy terminálu (ansi escape kódy)\">🌈",
		"tvt_ntail": "limit zpětného posouvání (kolik bajtů textu ponechat načtených)",

		"m3u_add1": "skladba přidána do m3u playlistu",
		"m3u_addn": "{0} skladeb přidáno do m3u playlistu",
		"m3u_clip": "m3u playlist nyní zkopírován do schránky\n\nměli byste vytvořit nový textový soubor pojmenovaný něco.m3u a vložit playlist do tohoto dokumentu; toto ho učiní přehratelným",

		"gt_vau": "nezobrazovat videa, jen přehrát zvuk\">🎧",
		"gt_msel": "povolit výběr souborů; ctrl-klik na soubor pro přepsání$N$N&lt;em&gt;když aktivní: dvojklik na soubor / složku pro otevření&lt;/em&gt;$N$NKlávesová zkratka: S\">výběr více",
		"gt_crop": "ořez náhledů na střed\">ořez",
		"gt_3x": "náhledy s vysokým rozlišením\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "rozdělit",
		"gt_sort": "řadit podle",
		"gt_name": "název",
		"gt_sz": "velikost",
		"gt_ts": "datum",
		"gt_ext": "typ",
		"gt_c1": "více zkrátit názvy souborů (zobrazit méně)",
		"gt_c2": "méně zkrátit názvy souborů (zobrazit více)",

		"sm_w8": "hledám...",
		"sm_prev": "výsledky hledání níže jsou z předchozího dotazu:\n  ",
		"sl_close": "zavřít výsledky hledání",
		"sl_hits": "zobrazuji {0} zásahů",
		"sl_moar": "načíst více",

		"s_sz": "velikost",
		"s_dt": "datum",
		"s_rd": "cesta",
		"s_fn": "název",
		"s_ta": "tagy",
		"s_ua": "nahráno@",
		"s_ad": "pokročilé",
		"s_s1": "minimum MiB",
		"s_s2": "maximum MiB",
		"s_d1": "min. iso8601",
		"s_d2": "max. iso8601",
		"s_u1": "nahráno po",
		"s_u2": "a/nebo před",
		"s_r1": "cesta obsahuje &nbsp; (oddělené mezerami)",
		"s_f1": "název obsahuje &nbsp; (negace s -ne)",
		"s_t1": "tagy obsahují &nbsp; (^=začátek, konec=$)",
		"s_a1": "specifické vlastnosti metadat",

		"md_eshow": "nelze vykreslit ",
		"md_off": "[📜<em>readme</em>] zakázáno v [⚙️] -- dokument skryt",

		"badreply": "Selhalo parsování odpovědi ze serveru",

		"xhr403": "403: Přístup odepřen\n\nzkuste stisknout F5, možná jste se odhlásili",
		"xhr0": "neznámý (pravděpodobně ztraceno spojení se serverem, nebo server je offline)",
		"cf_ok": "omlouváme se za to -- DD" + wah + "oS ochrana se aktivovala\n\nvěci by se měly obnovit asi za 30 sekund\n\npokud se nic nestane, stiskněte F5 pro obnovení stránky",
		"tl_xe1": "nelze vypsat podsložky:\n\nchyba ",
		"tl_xe2": "404: Složka nenalezena",
		"fl_xe1": "nelze vypsat soubory ve složce:\n\nchyba ",
		"fl_xe2": "404: Složka nenalezena",
		"fd_xe1": "nelze vytvořit podsložku:\n\nchyba ",
		"fd_xe2": "404: Nadřazená složka nenalezena",
		"fsm_xe1": "nelze odeslat zprávu:\n\nchyba ",
		"fsm_xe2": "404: Nadřazená složka nenalezena",
		"fu_xe1": "selhalo načtení unpost seznamu ze serveru:\n\nchyba ",
		"fu_xe2": "404: Soubor nenalezen??",

		"fz_tar": "nekomprimovaný gnu-tar soubor (linux / mac)",
		"fz_pax": "nekomprimovaný tar formátu pax (pomalejší)",
		"fz_targz": "gnu-tar s gzip kompresí úrovně 3$N$Nto je obvykle velmi pomalé, takže$Npoužijte místo toho nekomprimovaný tar",
		"fz_tarxz": "gnu-tar s xz kompresí úrovně 1$N$Nto je obvykle velmi pomalé, takže$Npoužijte místo toho nekomprimovaný tar",
		"fz_zip8": "zip s utf8 názvy souborů (možná problematické na windows 7 a starších)",
		"fz_zipd": "zip s tradičními cp437 názvy souborů, pro opravdu starý software",
		"fz_zipc": "cp437 s crc32 vypočítaným brzy,$Npro MS-DOS PKZIP v2.04g (říjen 1993)$N(trvá déle zpracovat před začátkem stahování)",

		"un_m1": "můžete smazat vaše nedávné nahrání (nebo zrušit nedokončené) níže",
		"un_upd": "obnovit",
		"un_m4": "nebo sdílet soubory viditelné níže:",
		"un_ulist": "zobrazit",
		"un_ucopy": "kopírovat",
		"un_flt": "volitelný filtr:&nbsp; URL musí obsahovat",
		"un_fclr": "vymazat filtr",
		"un_derr": 'unpost-delete selhalo:\n',
		"un_f5": 'něco se pokazilo, zkuste prosím obnovit, nebo stiskněte F5',
		"un_uf5": "omlouváme se ale musíte obnovit stránku (například stisknutím F5 nebo CTRL-R) předtím než toto nahrávání může být zrušeno",
		"un_nou": '<b>varování:</b> server je příliš zaneprázdněn pro zobrazení nedokončených nahrávání; za chvíli klikněte na odkaz "obnovit"',
		"un_noc": '<b>varování:</b> unpost plně nahraných souborů není povoleno/dovoleno v konfiguraci serveru',
		"un_max": "zobrazuji prvních 2000 souborů (použijte filtr)",
		"un_avail": "{0} nedávných nahrávání může být smazáno<br />{1} nedokončených může být zrušeno",
		"un_m2": "řazeno podle času nahrávání; nejnovější první:",
		"un_no1": "počkej! žádná nahrávání nejsou dostatečně nedávná",
		"un_no2": "počkej! žádná nahrávání odpovídající tomuto filtru nejsou dostatečně nedávná",
		"un_next": "smazat dalších {0} souborů níže",
		"un_abrt": "zrušit",
		"un_del": "smazat",
		"un_m3": "načítám vaše nedávné nahrání...",
		"un_busy": "mažu {0} souborů...",
		"un_clip": "{0} odkazů zkopírováno do schránky",

		"u_https1": "měli byste",
		"u_https2": "přejít na https",
		"u_https3": "pro lepší výkon",
		"u_ancient": "váš prohlížeč je úctyhodně starý -- možná byste měli <a href=\"#\" onclick=\"goto('bup')\">použít bup</a>",
		"u_nowork": "vyžadován firefox 53+ nebo chrome 57+ nebo iOS 11+",
		"tail_2old": "vyžadován firefox 105+ nebo chrome 71+ nebo iOS 14.5+",
		"u_nodrop": "váš prohlížeč je příliš starý pro nahrávání přetažením (drag-and-drop)",
		"u_notdir": "toto není složka!\n\nváš prohlížeč je příliš starý,\nzkuste prosím soubory přetáhnout",
		"u_uri": "pro přetažení obrázků z jiných oken prohlížeče,\nje prosím přetáhněte na velké tlačítko pro nahrávání",
		"u_enpot": "přepnout na <a href=\"#\">potato UI</a> (může zrychlit nahrávání)",
		"u_depot": "přepnout na <a href=\"#\">fancy UI</a> (může zpomalit nahrávání)",
		"u_gotpot": "přepínám na potato UI pro zrychlení nahrávání,\n\npokud nesouhlasíte, klidně jej přepněte zpět!",
		"u_pott": "<p>soubory: &nbsp; <b>{0}</b> dokončeno, &nbsp; <b>{1}</b> selhalo, &nbsp; <b>{2}</b> nahrává se, &nbsp; <b>{3}</b> ve frontě</p>",
		"u_ever": "toto je základní nahrávání; up2k vyžaduje alespoň<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": "toto je základní nahrávání; <a href=\"#\" id=\"u2yea\">up2k</a> je lepší",
		"u_uput": "optimalizovat pro rychlost (přeskočit kontrolní součet)",
		"u_ewrite": "nemáte oprávnění k zápisu do této složky",
		"u_eread": "nemáte oprávnění ke čtení této složky",
		"u_enoi": "vyhledávání souborů není povoleno v konfiguraci serveru",
		"u_enoow": "přepsání zde nebude fungovat; je vyžadováno oprávnění k mazání",
		"u_badf": "Těchto {0} souborů (z celkem {1}) bylo přeskočeno, pravděpodobně kvůli oprávněním v souborovém systému:\n\n",
		"u_blankf": "Těchto {0} souborů (z celkem {1}) je prázdných; přesto je nahrát?\n\n",
		"u_applef": "Těchto {0} souborů (z celkem {1}) je pravděpodobně nežádoucích;\nStiskněte <code>OK/Enter</code> pro PŘESKOČENÍ následujících souborů,\nStiskněte <code>Zrušit/ESC</code> pro Zahrnutí a NAHRÁNÍ i těchto souborů:\n\n",
		"u_just1": "\nMožná to bude fungovat lépe, když vyberete pouze jeden soubor",
		"u_ff_many": "pokud používáte <b>Linux / MacOS / Android,</b> takové množství souborů <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>může</em> shodit Firefox!</a>\npokud se to stane, zkuste to prosím znovu (nebo použijte Chrome).",
		"u_up_life": "Tento upload bude smazán ze serveru\n{0} po jeho dokončení",
		"u_asku": "Nahrát {0} souborů do <code>{1}</code>",
		"u_unpt": "toto nahrávání můžete vrátit zpět / smazat pomocí 🧯 vlevo nahoře",
		"u_bigtab": "chystám se zobrazit {0} souborů\n\nto může shodit váš prohlížeč, jste si jisti?",
		"u_scan": "Skenuji soubory...",
		"u_dirstuck": "procházení adresáře se zaseklo při pokusu o přístup k následujícím {0} položkám; budou přeskočeny:",
		"u_etadone": "Hotovo ({0}, {1} souborů)",
		"u_etaprep": "(příprava na nahrávání)",
		"u_hashdone": "hashování dokončeno",
		"u_hashing": "hashování",
		"u_hs": "navazuji spojení...",
		"u_started": "soubory se nyní nahrávají; viz [🚀]",
		"u_dupdefer": "duplikát; bude zpracován po všech ostatních souborech",
		"u_actx": "klikněte na tento text, abyste zabránili ztrátě<br />výkonu při přepínání do jiných oken/záložek",
		"u_fixed": "OK!&nbsp; Opraveno 👍",
		"u_cuerr": "nepodařilo se nahrát část {0} z {1};\npatrně neškodné, pokračuji\n\nsoubor: {2}",
		"u_cuerr2": "server odmítl nahrání (část {0} z {1});\nzopakuji později\n\nsoubor: {2}\n\nchyba ",
		"u_ehstmp": "zopakuji pokus; viz vpravo dole",
		"u_ehsfin": "server odmítl požadavek na dokončení nahrávání; opakuji pokus...",
		"u_ehssrch": "server odmítl požadavek na vyhledávání; opakuji pokus...",
		"u_ehsinit": "server odmítl požadavek na zahájení nahrávání; opakuji pokus...",
		"u_eneths": "síťová chyba při navazování spojení pro nahrávání; opakuji pokus...",
		"u_enethd": "síťová chyba při ověřování existence cíle; opakuji pokus...",
		"u_cbusy": "čekám, až nám server po síťovém problému začne znovu důvěřovat...",
		"u_ehsdf": "na serveru došlo místo na disku!\n\nbudu to zkoušet dál, pro případ, že někdo\nuvolní dostatek místa pro pokračování",
		"u_emtleak1": "vypadá to, že váš webový prohlížeč může mít únik paměti (memory leak);\nprosím",
		"u_emtleak2": " <a href=\"{0}\">přejděte na https (doporučeno)</a> nebo ",
		"u_emtleak3": " ",
		"u_emtleakc": "zkuste následující:\n<ul><li>stiskněte <code>F5</code> pro obnovení stránky</li><li>poté vypněte tlačítko &nbsp;<code>mt</code>&nbsp; v &nbsp;<code>⚙️ nastavení</code></li><li>a zkuste nahrávání znovu</li></ul>Nahrávání bude o něco pomalejší, ale co se dá dělat.\nOmlouváme se za potíže!\n\nPS: chrome v107 <a href=\"https://bugs.chromium.org/p/chromium/issues/detail?id=1354816\" target=\"_blank\">obsahuje opravu</a> pro tento problém",
		"u_emtleakf": "zkuste následující:\n<ul><li>stiskněte <code>F5</code> pro obnovení stránky</li><li>poté zapněte <code>🥔</code> (potato) v rozhraní nahrávání<li>a zkuste nahrávání znovu</li></ul>\nPS: firefox snad <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\">bude mít opravu</a> v některé z příštích verzí",
		"u_s404": "nenalezeno na serveru",
		"u_expl": "vysvětlit",
		"u_maxconn": "většina prohlížečů omezuje počet na 6, ale firefox umožňuje toto navýšit pomocí <code>connections-per-server</code> v <code>about:config</code>",
		"u_tu": "<p class=\"warn\">VAROVÁNÍ: turbo zapnuto, <span>&nbsp;klient nemusí detekovat a obnovit nedokončené nahrávání; viz nápovědu u tlačítka turbo</span></p>",
		"u_ts": "<p class=\"warn\">VAROVÁNÍ: turbo zapnuto, <span>&nbsp;výsledky vyhledávání mohou být nesprávné; viz nápovědu u tlačítka turbo</span></p>",
		"u_turbo_c": "turbo je vypnuto v konfiguraci serveru",
		"u_turbo_g": "vypínám turbo, protože nemáte oprávnění\nk výpisu adresářů na tomto svazku",
		"u_life_cfg": 'automatické smazání po <input id="lifem" p="60" /> min (nebo <input id="lifeh" p="3600" /> hodinách)',
		"u_life_est": 'nahrání bude smazáno <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'tato složka vynucuje\nmax. životnost {0}',
		"u_unp_ok": 'unpost je povoleno pro {0}',
		"u_unp_ng": 'unpost NEBUDE povoleno',
		"ue_ro": 'váš přístup k této složce je pouze pro čtení\n\n',
		"ue_nl": 'momentálně nejste přihlášeni',
		"ue_la": 'momentálně jste přihlášeni jako "{0}"',
		"ue_sr": 'momentálně jste v režimu vyhledávání souborů\n\npřepněte do režimu nahrávání kliknutím na lupu 🔎 (vedle velkého tlačítka HLEDAT) a zkuste nahrávání znovu\n\nomlouváme se',
		"ue_ta": 'zkuste nahrávání znovu, nyní by to mělo fungovat',
		"ue_ab": "tento soubor se již nahrává do jiné složky a toto nahrávání musí být dokončeno předtím, než může být soubor nahrán jinam.\n\nMůžete zrušit a zapomenout na původní nahrávání pomocí levého horního 🧯",
		"ur_1uo": "OK: Soubor úspěšně nahrán",
		"ur_auo": "OK: Všech {0} souborů úspěšně nahráno",
		"ur_1so": "OK: Soubor nalezen na serveru",
		"ur_aso": "OK: Všech {0} souborů nalezeno na serveru",
		"ur_1un": "Nahrání selhalo, omlouváme se",
		"ur_aun": "Všech {0} nahrání selhalo, omlouváme se",
		"ur_1sn": "Soubor NEBYL nalezen na serveru",
		"ur_asn": "{0} souborů NEBYLO nalezeno na serveru",
		"ur_um": "Dokončeno;\n{0} nahrání OK,\n{1} nahrání selhalo, omlouváme se",
		"ur_sm": "Dokončeno;\n{0} souborů nalezeno na serveru,\n{1} souborů NENALEZENO na serveru",

		"lang_set": "obnovit stránku, aby se změna projevila?",
	},
	"deu": {
		"tt": "Deutsch",

		"cols": {
			"c": "Aktionen",
			"dur": "Dauer",
			"q": "Qualität / Bitrate",
			"Ac": "Audiocodec",
			"Vc": "Videocodec",
			"Fmt": "Format / Container",
			"Ahash": "Audio Checksumme",
			"Vhash": "Video Checksumme",
			"Res": "Auflösung",
			"T": "Dateityp",
			"aq": "Audioqualität / Bitrate",
			"vq": "Videoqualität / Bitrate",
			"pixfmt": "Subsampling / Pixelstruktur",
			"resw": "horizontale Auflösung",
			"resh": "vertikale Auflösung",
			"chs": "Audiokanäle",
			"hz": "Abtastrate"
		},

		"hks": [
			[
				"misc",
				["ESC", "Dinge schliessen"],

				"file-manager",
				["G", "zwischen Liste und Gitter wechseln"],
				["T", "zwischen Vorschaubildern und Symbolen wechseln"],
				["⇧ A/D", "Vorschaubildergrösse ändern"],
				["STRG-K", "Auswahl löschen"],
				["STRG-X", "Auswahl ausschneiden"],
				["STRG-C", "Auswahl in Zwischenablage kopieren"],
				["STRG-V", "Zwischenablage hier einfügen"],
				["Y", "Auswahl herunterladen"],
				["F2", "Auswahl umbenennen"],

				"file-list-sel",
				["LEER", "Dateiauswahl aktivieren"],
				["↑/↓", "Cursor verschieben"],
				["STRG ↑/↓", "Cursor und Bildschirm verschieben"],
				["⇧ ↑/↓", "Vorherige / nächste Datei auswählen"],
				["STRG-A", "Alle Dateien / Ordner auswählen"],
			], [
				"navigation",
				["B", "Zwischen Brotkrumen und Navpane wechseln"],
				["I/K", "vorheriger / nächster Ordner"],
				["M", "übergeordneter Ordner (oder Vorherigen einklappen)"],
				["V", "Zwischen Textdateien und Navpane wechseln"],
				["A/D", "Grösse der Navpane ändern"],
			], [
				"audio-player",
				["J/L", "Vorheriger / nächster Song"],
				["U/O", "10 Sek. vor- / zurückspringen"],
				["0..9", "zu 0%..90% springen"],
				["P", "Wiedergabe / Pause"],
				["S", "aktuell abgespielten Song auswählen"],
				["Y", "Sing herunterladen"],
			], [
				"image-viewer",
				["J/L, ←/→", "vorheriges / nächstes Bild"],
				["Pos1/Ende", "erstes / letztes Bild"],
				["F", "Vollbild"],
				["R", "im Uhrzeigersinn drehen"],
				["⇧ R", "gegen den Uhrzeigensinn drehen"],
				["S", "Bild auswählen"],
				["Y", "Bild herunterladen"],
			], [
				"video-player",
				["U/O", "10 Sek. vor- / zurückspringen"],
				["P/K/LEER", "Wiedergabe / Pause"],
				["C", "continue playing next"],
				["V", "Wiederholungs-Wiedergabe (Loop)"],
				["M", "Stummschalten"],
				["[ und ]", "Loop-Interval einstellen"],
			], [
				"textfile-viewer",
				["I/K", "vorherige / nächste Datei"],
				["M", "Textdatei schliessen"],
				["E", "Textdatei bearbeiten"],
				["S", "Textdatei auswählen (für Ausschneiden / Kopieren / Umbenennen)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Abbrechen",

		"enable": "Aktivieren",
		"danger": "ACHTUNG",
		"clipped": "in Zwischenablage kopiert",

		"ht_s1": "Sekunde",
		"ht_s2": "Sekunden",
		"ht_m1": "Minute",
		"ht_m2": "Minuten",
		"ht_h1": "Stunde",
		"ht_h2": "Stunden",
		"ht_d1": "Tag",
		"ht_d2": "Tage",
		"ht_and": " und ",

		"goh": "Einstellungen",
		"gop": 'zum vorherigen Ordner springen">vorh.',
		"gou": 'zum übergeordneter Ordner springen">hoch',
		"gon": 'zum nächsten Ordner springen">nächst.',
		"logout": "Abmelden ",
		"login": "Anmelden", //m
		"access": " Zugriff",
		"ot_close": "Submenu schliessen",
		"ot_search": "Dateien nach Attributen, Pfad/Name, Musiktags oder beliebiger Kombination suchen$N$N&lt;code&gt;foo bar&lt;/code&gt; = muss «foo» und «bar» enthalten,$N&lt;code&gt;foo -bar&lt;/code&gt; = muss «foo» aber nicht «bar» enthalten,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = beginnt mit «yana» und ist «opus»-Datei$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = genau «try unite» enthalten$N$NDatumsformat ist iso-8601, z.B.$N&lt;code&gt;2009-12-31&lt;/code&gt; oder &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: lösche deine letzten Uploads oder breche unvollständige ab",
		"ot_bup": "bup: Basic Uploader, unterstützt sogar Neuheiten wie Netscape 4.0",
		"ot_mkdir": "mkdir: Neuen Ordner erstellen",
		"ot_md": "new-md: Neues Markdown-Dokument erstellen",
		"ot_msg": "msg: Eine Nachricht an das Server-Log schicken",
		"ot_mp": "Media Player-Optionen",
		"ot_cfg": "Konfigurationsoptionen",
		"ot_u2i": 'up2k: Dateien hochladen (wenn du Schreibrechte hast) oder in den Suchmodus wechseln, um zu prüfen, ob sie bereits auf dem Server existieren$N$NUploads sind fortsetzbar, multithreaded und behalten Dateizeitstempel, verbrauchen aber mehr CPU als [🎈]&nbsp; (der einfache Uploader)<br /><br />während Uploads wird dieses Symbol zu einem Fortschrittsanzeiger!',
		"ot_u2w": 'up2k: Dateien mit Wiederaufnahme-Unterstützung hochladen (Browser schließen und später dieselben Dateien erneut hochladen)$N$Nmultithreaded, behält Dateizeitstempel, verbraucht aber mehr CPU als [🎈]&nbsp; (der einfache Uploader)<br /><br />während Uploads wird dieses Symbol zu einem Fortschrittsanzeiger!',
		"ot_noie": 'Bitte benutze Chrome / Firefox / Edge',

		"ab_mkdir": "Ordner erstellen",
		"ab_mkdoc": "Markdown Doc erstellen",
		"ab_msg": "Nachricht an Server Log senden",

		"ay_path": "zu Ordnern springen",
		"ay_files": "zu Dateien springen",

		"wt_ren": "ausgewählte Elemente umbenennen$NHotkey: F2",
		"wt_del": "ausgewählte Elemente löschen$NHotkey: STRG-K",
		"wt_cut": "ausgewählte Elemente ausschneiden &lt;small&gt;(um sie dann irgendwo anders einzufügen)&lt;/small&gt;$NHotkey: STRG-X",
		"wt_cpy": "ausgewählte Elemente in Zwischenablage kopieren$N(um sie dann irgendwo anders einzufügen)$NHotkey: ctrl-C",
		"wt_pst": "zuvor ausgeschnittenen / kopierte Elemente einfügen$NHotkey: STRG-V",
		"wt_selall": "alle Dateien auswählen$NHotkey: STRG-A (wenn Datei fokusiert)",
		"wt_selinv": "Auswahl invertieren",
		"wt_zip1": "Diesen Ordner als Archiv herunterladen",
		"wt_selzip": "Auswahl als Archiv herunterladen",
		"wt_seldl": "Auswahl als separate Dateien herunterladen$NHotkey: Y",
		"wt_npirc": "kopiere Titelinfo als IRC-formattierten Text",
		"wt_nptxt": "kopiere Titelinfo als Text",
		"wt_m3ua": "Zu M3U-Wiedergabeliste hinzufügen (wähle später <code>📻copy</code>)",
		"wt_m3uc": "M3U-Wiedergabeliste in Zwischenablage kopieren",
		"wt_grid": "Zwischen Gitter und Liste wechseln$NHotkey: G",
		"wt_prev": "Vorheriger Titel$NHotkey: J",
		"wt_play": "Wiedergabe / Pause$NHotkey: P",
		"wt_next": "Nächster Titel$NHotkey: L",

		"ul_par": "Parallele Uploads:",
		"ut_rand": "Zufällige Dateinamen",
		"ut_u2ts": "Zuletzt geändert-Zeitstempel von$Ndeinem Dateisystem auf den Server übertragen\">📅",
		"ut_ow": "Existierende Dateien auf dem Server überschreiben?$N🛡️: Nie (generiert einen neuen Dateinamen)$N🕒: Überschreiben, wenn Server-Datei älter ist als meine$N♻️: Überschreiben, wenn der Dateiinhalt anders ist",
		"ut_mt": "Andere Dateien während des Uploads hashen$N$Nsolltest du deaktivieren, falls deine CPU oder Festplatte zum Flaschenhals werden könnte",
		"ut_ask": 'Vor dem Upload nach Bestätigung fragen">💭',
		"ut_pot": "Verbessert Upload-Geschwindigkeit$Nindem das UI weniger komplex gemacht wird",
		"ut_srch": "nicht wirklich hochladen, stattdessen prüfen ob Datei bereits auf dem Server existiert (scannt alle Ordner, die du lesen kannst)",
		"ut_par": "setze auf 0 zum Pausieren$N$Nerhöhe, wenn deine Verbindung langsam / instabil ist$N$lass auf 1 im LAN oder wenn die Festplatte auf dem Server ein Flaschenhals ist",
		"ul_btn": "Dateien / Ordner hier<br>ablegen (oder klick mich)",
		"ul_btnu": "U P L O A D",
		"ul_btns": "S U C H E N",

		"ul_hash": "hash",
		"ul_send": "senden",
		"ul_done": "fertig",
		"ul_idle1": "keine Uploads in der Warteschlange",
		"ut_etah": "durchschnittl. &lt;em&gt;hashing&lt;/em&gt; Geschw. &amp; gesch. Restzeit",
		"ut_etau": "durchschnittl. &lt;em&gt;upload&lt;/em&gt; Geschw. &amp; gesch. Restzeit",
		"ut_etat": "durchschnittl. &lt;em&gt;total&lt;/em&gt; Geschw. &amp; gesch. Restzeit",

		"uct_ok": "Erfolgreich abgeschlossen",
		"uct_ng": "no-good: fehlgeschlagen / abgelehnt / nicht gefunden",
		"uct_done": "ok and ng zusammen",
		"uct_bz": "wird gehasht oder hochgeladen",
		"uct_q": "ausstehend",

		"utl_name": "Dateiname",
		"utl_ulist": "Liste",
		"utl_ucopy": "kopieren",
		"utl_links": "Links",
		"utl_stat": "Status",
		"utl_prog": "Fortschritt",

		// keep short:
		"utl_404": "404",
		"utl_err": "Fehler",
		"utl_oserr": "OS-Fehler",
		"utl_found": "gefunden",
		"utl_defer": "zurückstellen",
		"utl_yolo": "YOLO",
		"utl_done": "fertig",

		"ul_flagblk": "Die Dateien wurden zur Warteschlange hinzugefügt</b><br>jedoch ist up2k gerade in einem anderen Browsertab aktiv.<br>Ich warte, bis der Upload abgeschlossen ist.",
		"ul_btnlk": "Die Serverkonfiguration hat diese Einstellung gesperrt",

		"udt_up": "Upload",
		"udt_srch": "Suchen",
		"udt_drop": "hier ablegen",

		"u_nav_m": '<h6>okay, was gibts??</h6><code>Eingabe</code> = Dateien (1 oder mehr)\n<code>ESC</code> = 1 Ordner (inkl. Unterordner)',
		"u_nav_b": '<a href="#" id="modal-ok">Dateien</a><a href="#" id="modal-ng">1 Ordner</a>',

		"cl_opts": "Schalter",
		"cl_themes": "Themes",
		"cl_langs": "Sprache",
		"cl_ziptype": "Ordner Download",
		"cl_uopts": "up2k Schalter",
		"cl_favico": "Favicon",
		"cl_bigdir": "grosse Ordner",
		"cl_hsort": "#sort",
		"cl_keytype": "Schlüsselnotation",
		"cl_hiddenc": "Spalten verstecken",
		"cl_hidec": "verstecken",
		"cl_reset": "zurücksetzen",
		"cl_hpick": "zum Verstecken, tippe auf Spaltenüberschriften in der Tabelle unten",
		"cl_hcancel": "Spaltenbearbeitung abgebrochen",

		"ct_grid": '田 Das Raster&trade;',
		"ct_ttips": '◔ ◡ ◔">ℹ️ Tooltips',
		"ct_thumb": 'In Raster-Ansicht, zwischen Icons und Vorschau wechseln$NHotkey: T">🖼️ Vorschaubilder',
		"ct_csel": 'Benutze STRG und UMSCHALT für Dateiauswahl in Raster-Ansicht">sel',
		"ct_ihop": 'Wenn die Bildanzeige geschlossen ist, scrolle runter zu den zuletzt angesehenen Dateien">g⮯',
		"ct_dots": 'Verstecke Dateien anzeigen (wenn erlaubt durch Server)">dotfiles',
		"ct_qdel": 'Nur einmal fragen, wenn mehrere Dateien gelöscht werden">qdel',
		"ct_dir1st": 'Ordner vor Dateien sortieren">📁 zuerst',
		"ct_nsort": 'Natürliche Sortierung (für Dateinamen mit führenden Ziffern)">nsort',
		"ct_utc": 'Verwenden Sie UTC für alle Zeitangaben">UTC', //m
		"ct_readme": 'README.md in Dateiliste anzeigen">📜 readme',
		"ct_idxh": 'index.html anstelle von Dateiliste anzeigen">htm',
		"ct_sbars": 'Scrollbars zeigen">⟊',

		"cut_umod": "Sollte die Datei bereits auf dem Server existieren, den 'Zuletzt geändert'-Zeitstempel an deine lokale Datei anpassen (benötigt Lese- und Löschrechte)\">re📅",

		"cut_turbo": "der YOLO-Knopf, den du wahrscheinlich NICHT aktivieren willst:$N$NBenutze ihn, falls du ne Menge Zeug hochladen wolltest und aus irgendeinem Grund neustarten musstest und du so schnell wie möglich weitermachen willst.$N$Ndies ersetzt den Hash-Check mit einem einfachen <em>&quot;Ist die Datei auf dem Server gleich gross?&quot;</em>, wenn die Datei also anderen Inhalt hat, wird sie NICHT nochmal hochgeladen!$N$NDu solltest dieses Feature ausschalten, sobald der Upload fertig ist und dann die gleichen Dateien nochmal &quot;hochladen&quot;, damit der Client sie verifizieren kann.\">turbo",

		"cut_datechk": "Funktioniert nur in kombination mit dem Turbo-Knopf$N$NReduziert den YOLO-Faktor ein bisschen; prüft, ob der Zeitstempel deiner Datei mit dem auf dem Server übereinstimmt$N$Nsollte <em>theoretisch</em> die meisten unfertigen / korrupten Uploads erwischen, ist aber nicht zu gebrauchen, um einen Prüfdurchgang nach einem Turbo-Upload zu machen\">date-chk",

		"cut_u2sz": "Grösse (in MiB) für jeden Upload-Chunk; mit grossen Werten fliegen die Bits besser über den Atlantik. Versuche kleine Werte, wenn du eine schlechte Verbindung hast (z.B. du benutzt mobile Daten in Deutschland)",

		"cut_flag": "Stelle sicher, dass nur ein Tab auf einmal Dateien hochlädt$N -- andere Tabs müssen diese Funktion auch aktiviert haben $N -- funktioniert nur bei Tabs mit der gleichen Domäne",

		"cut_az": "Lädt Dateien in alphabetischer Reihenfolge hoch, anstatt nach Dateigrösse$N$NAlphabethische Reihenfolge kann es einfacher machen, Server-Fehler mit naktem Auge zu erkennen, macht aber Uploads über Glassfaser / LAN etwas langsamer",

		"cut_nag": "Benachrichtigung über das Betriebssystem abgeben, wenn Upload fertig ist$N(nur wenn Browser oder Tab nicht im Vordergrund ist)",
		"cut_sfx": "Spielt ein Ton ab, wenn Upload fertig ist$N(nur wenn Browser oder Tab nicht im Vordergrund ist)",

		"cut_mt": "Multithreading benutzen um Datei-Hashing zu beschleunigen$N$NDies nutzt Web-Workers und benötigt$Nmehr RAM (bis zu 512 MiB extra)$N$Nbeschleunigt HTTPS 30% schneller, HTTP um 4.5x\">mt",

		"cut_wasm": "benutzt WASM anstelle des Browser-eigenen Hashers; verbessert Geschwindigkeit auf Chromium-basierten Browsern, erhöht aber die CPU-Auslastung. Viele ältere Versionen von Chrome haben Memory-Leaks, die den gesamten RAM verbrauchen und dann crashen, wenn diese Funktion aktiviert ist.\">wasm",

		"cft_text": "Favicon Text (leer lassen und neuladen zum Deaktivieren)",
		"cft_fg": "Vordergrundfarbe",
		"cft_bg": "Hintergrundfarbe",

		"cdt_lim": "max. Anz. Dateien, die in einem Ordner gezeigt werden sollen",
		"cdt_ask": "beim Runterscrollen nach $NAktion fragen statt mehr,$NDateien zu laden",
		"cdt_hsort": "Menge an Sortierregeln (&lt;code&gt;,sorthref&lt;/code&gt;) in Media-URLs enthalten sein sollen. Ein Wert von 0 sorgt dafür, dass Sortierregeln in Media-URLs ignoriert werden",

		"tt_entree": "Navpane anzeigen (Ordnerbaum Sidebar)$NHotkey: B",
		"tt_detree": "Breadcrumbs anzeigen$NHotkey: B",
		"tt_visdir": "zu ausgewähltem Ordner scrollen",
		"tt_ftree": "zw. Ordnerbaum / Textdateien wechseln$NHotkey: V",
		"tt_pdock": "übergeordnete Ordner in einem angedockten Fenster oben anzeigen",
		"tt_dynt": "autom. wachsen wenn Baum wächst",
		"tt_wrap": "Zeilenumbruch",
		"tt_hover": "Beim Hovern überlange Zeilen anzeigen$N(Scrollen funktioniert nicht ausser $N&nbsp; Cursor ist im linken Gutter)",

		"ml_pmode": "am Ende des Ordners...",
		"ml_btns": "cmds",
		"ml_tcode": "transcodieren",
		"ml_tcode2": "transcodieren zu",
		"ml_tint": "färben",
		"ml_eq": "Audio Equalizer",
		"ml_drc": "Dynamic Range Compressor",

		"mt_loop": "Song wiederholen\">🔁",
		"mt_one": "Wiedergabe nach diesem Song beenden\">1️⃣",
		"mt_shuf": "Zufällige Wiedergabe im Ordner\">🔀",
		"mt_aplay": "automatisch abspielen, wenn der Link, mit dem du auf den Server zugreifst, eine Titel-ID enthält$N$NDeaktivieren verhindert auch, dass die Seiten-URL bei Musikwiedergabe mit Titel-IDs aktualisiert wird, um Autoplay zu verhindern, falls diese Einstellungen verloren gehen, die URL aber bestehen bleibt\">a▶",
		"mt_preload": "nächsten Titel gegen Ende vorladen für nahtlose Wiedergabe\">Vorladen",
		"mt_prescan": "vor Ende des letzten Titels zum nächsten Ordner wechseln,$Ndamit der Browser die$NWiedergabe nicht stoppt\">Navigation",
		"mt_fullpre": "versuchen, den gesamten Titel vorzuladen;$N✅ bei <b>unzuverlässiger</b> Verbindung aktivieren,$N❌ bei langsamer Verbindung deaktivieren\">vollst&auml;ndig",
		"mt_fau": "auf Handys verhindern, dass Musik stoppt, wenn der nächste Titel nicht schnell genug vorlädt (kann zu fehlerhafter Tag-Anzeige führen)\">☕️",
		"mt_waves": "Wellenform-Suchleiste:$NAudio-Amplitude in der Leiste anzeigen\">~s",
		"mt_npclip": "Buttons zum Kopieren des aktuellen Titels anzeigen\">/np",
		"mt_m3u_c": "Buttons zum Kopieren der$Nausgewählten Titel als m3u8-Wiedergabeliste anzeigen\">📻",
		"mt_octl": "OS-Integration (Media-Hotkeys/OSD)\">os-ctl",
		"mt_oseek": "Suchen via OS-Integration erlauben$N$NHinweis: auf einigen Geräten (iPhones)$Nersetzt dies den nächsten-Titel-Button\">Suchen",
		"mt_oscv": "Albumcover in OSD anzeigen\">Cover",
		"mt_follow": "den spielenden Titel im Blick behalten\">🎯",
		"mt_compact": "kompakte Steuerelemente\">⟎",
		"mt_uncache": "Cache leeren &nbsp;(probier das, wenn dein Browser$Neine defekte Kopie eines Titels zwischenspeichert und sich weigert, ihn abzuspielen)\">Cache leeren",
		"mt_mloop": "offenen Ordner wiederholen\">🔁 Schleife",
		"mt_mnext": "nächsten Ordner laden und fortfahren\">📂 nächster",
		"mt_mstop": "Wiedergabe beenden\">⏸ Stop",
		"mt_cflac": "FLAC / WAV zu {0} konvertierebn\">flac",
		"mt_caac": "AAC / M4A zu {0} konvertieren\">aac",
		"mt_coth": "Convertiere alle Dateien (die nicht MP3 sind) zu {0}\">oth",
		"mt_c2opus": "Beste Wahl für Desktops, Laptops, Android\">opus",
		"mt_c2owa": "opus-weba, für iOS 17.5 und neuer\">owa",
		"mt_c2caf": "opus-caf, für iOS 11 bis 17\">caf",
		"mt_c2mp3": "benutze dieses Format für ältere Geräte\">mp3",
		"mt_c2flac": "beste Klangqualität, aber große Downloads\">flac", //m
		"mt_c2wav": "unkomprimierte Wiedergabe (noch größer)\">wav", //m
		"mt_c2ok": "Gute Wahl, Chef!",
		"mt_c2nd": "Das ist nicht das empfohlene Ausgabeformat für dein Gerät, aber passt schon",
		"mt_c2ng": "Dein Gerät scheint dieses Ausgabeformat nicht zu unterstützen, aber lass trotzdem mal probieren",
		"mt_xowa": "Es gibt Bugs in iOS, die die Hintergrund-Wiedergabe mit diesem Format verhindern; bitte nutze caf oder mp3 stattdessen",
		"mt_tint": "Hintergrundlevel (0-100) auf der Seekbar$Num Buffern weniger ablenkend zu machen",
		"mt_eq": "Aktiviert Equalizer und Lautstärkeregelung;$N$Nboost &lt;code&gt;0&lt;/code&gt; = Standard 100% Lautstärke (unverändert)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = Standard Stereo (unverändert)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% Links-Rechts-Crossfeed$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = Mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = Gesangsentfernung :^)$N$NDer Equalizer macht nahtlose Alben vollständig nahtlos, also lass' ihn mit allen Werten auf Null (außer width = 1) aktiviert, wenn dir das wichtig ist",
		"mt_drc": "Aktiviert den Dynamic Range Compressor (Lautstärkeglättung/-begrenzung); aktiviert auch den Equalizer zum Ausgleich, setze alle EQ-Felder außer 'width' auf 0, wenn du das nicht willst$N$Nsenkt die Lautstärke von Audio über SCHWELLENWERT dB; für jedes VERHÄLTNIS dB über SCHWELLENWERT gibt es 1 dB Ausgabe, also bedeuten Standardwerte von tresh -24 und ratio 12, dass es nie lauter als -22 dB werden sollte und der Equalizer-Boost sicher auf 0.8 oder sogar 1.8 mit ATK 0 und einem großen RLS wie 90 erhöht werden kann (funktioniert nur in Firefox; in anderen Browsern ist RLS max. 1)$N$N(siehe Wikipedia, dort wird es viel besser erklärt)",

		"mb_play": "Abspielen",
		"mm_hashplay": "Diese Audiodatei abspielen?",
		"mm_m3u": "Drücke <code>Eingabe/OK</code> zum Abspielen\nDrücke <code>ESC/Abbrechen</code> zum Bearbeiten",
		"mp_breq": "Benötigt Firefox 82+ oder Chrome 73+ oder iOS 15+",
		"mm_bload": "Lädt...",
		"mm_bconv": "Konvertiere zu {0}, bitte warte...",
		"mm_opusen": "Dein Browser kann AAC- / M4A-Dateien nicht abspielen;\nUmwandlung zu Opus ist jetzt aktiv",
		"mm_playerr": "Wiedergabefehler: ",
		"mm_eabrt": "Der Wiedergabeversuch wurde abgebrochen",
		"mm_enet": "Dein Internet läuft auf Edge, wa?",
		"mm_edec": "Die Datei scheint beschädigt zu sein??",
		"mm_esupp": "Dein Browser versteht dieses Audioformat nicht",
		"mm_eunk": "Unbekannter Fehler",
		"mm_e404": "Konnte Datei nicht abspielen; Fehler 404: Datei nicht gefunden.",
		"mm_e403": "Konnte Datei nicht abspielen; Fehler 403: Zugriff verweigert.\n\nDrücke F5 zum Neuladen, vielleicht wurdest du abgemeldet",
		"mm_e500": "Konnte Datei nicht abspielen; Fehler 500: Prüfe die Serverlogs.",
		"mm_e5xx": "Konnte Datei nicht abspielen; Server Fehler ",
		"mm_nof": "finde keine weiteren Audiodateien in der Nähe",
		"mm_prescan": "Suche nach Musik zum Abspielen...",
		"mm_scank": "Nächster Song gefunden:",
		"mm_uncache": "Cache geleert; Alle Songs werden beim nächsten Abspielversuch neu heruntergeladen",
		"mm_hnf": "dieser Song existiert nicht mehr",

		"im_hnf": "dieses Bild existiert nicht mehr",

		"f_empty": 'Dieser Ordner ist leer',
		"f_chide": 'Dies blendet die Spalte «{0}» aus\n\nDu kannst Spalten in den Einstellungen wieder einblenden.',
		"f_bigtxt": "Diese Datei ist {0} MiB gross -- Sicher, dass du sie als Text anzeigen willst?",
		"f_bigtxt2": "Möchtest du stattdessen nur das Ende der Datei anzeigen? Das aktiviert ausserdem die Folgen- und Verfolgen-Funktion, welche neu hinzugefügte Textzeilen in Echtzeit anzeigt",
		"fbd_more": '<div id="blazy">zeige <code>{0}</code> von <code>{1}</code> Dateien; <a href="#" id="bd_more">{2} anzeigen</a> oder <a href="#" id="bd_all">alle anzeigen</a></div>',
		"fbd_all": '<div id="blazy">zeige <code>{0}</code> von <code>{1}</code> Dateien; <a href="#" id="bd_all">alle anzeigen</a></div>',
		"f_anota": "nur {0} der {1} Elemente wurden ausgewählt;\num den gesamten Ordner auszuwählen, zuerst nach unten scrollen",

		"f_dls": 'die Dateilinks im aktuellen Ordner wurden\nin Downloadlinks geändert',

		"f_partial": "Um eine Datei sicher herunterzuladen, die gerade hochgeladen wird, klicke bitte die Datei mit dem gleichen Namen, aber ohne die <code>.PARTIAL</code>-Endung. Bitte drücke Abbrechen oder Escape, um dies zu tun.\n\nWenn du auf OK / Eingabe drückst, ignorierst du diese Warnung und lädst die <code>.PARTIAL</code>-Datei herunter, die ziemlich sicher beschädigte Daten enthält.",

		"ft_paste": "{0} Elemente einfügen$NHotkey: STRG-V",
		"fr_eperm": 'Umbenennen fehlgeschlagen:\nDir fehlt die "Verschieben"-Berechtigung in diesem Ordner',
		"fd_eperm": 'Löschen fehlgeschlagen:\nDir fehlt die "Löschen"-Berechtigung in diesem Ordner',
		"fc_eperm": 'Ausschneiden fehlgeschlagen:\nDir fehlt die "Verschieben"-Berechtigung in diesem Ordner',
		"fp_eperm": 'Einfügen fehlgeschlagen:\nDir fehlt die "Schreiben"-Berechtigung in diesem Ordner',
		"fr_emore": "Wähle mindestens ein Element zum Umbenennen aus",
		"fd_emore": "Wähle mindestens ein Element zum Löschen aus",
		"fc_emore": "Wähle mindestens ein Element zum Ausschneiden aus",
		"fcp_emore": "Wähle mindestens ein Element aus, um es in die Zwischenablage zu kopieren",

		"fs_sc": "Teile diesen Ordner",
		"fs_ss": "Teile die ausgewählten Dateien",
		"fs_just1d": "Du kannst nicht mehrere Ordner auswählen \noder Dateien und Ordner in der Auswahl mischen.",
		"fs_abrt": "❌ Abbrechen",
		"fs_rand": "🎲 Zufallsname",
		"fs_go": "✅ Share erstellen",
		"fs_name": "Name",
		"fs_src": "Quelle",
		"fs_pwd": "Passwort",
		"fs_exp": "Ablauf",
		"fs_tmin": "Minuten",
		"fs_thrs": "Stunden",
		"fs_tdays": "Tage",
		"fs_never": "nie",
		"fs_pname": "optionaler Linkname; zufällig wenn leer",
		"fs_tsrc": "zu teilende Datei oder Ordner",
		"fs_ppwd": "optionales Passwort",
		"fs_w8": "erstelle Share...",
		"fs_ok": "drücke <code>Eingabe/OK</code> für Zwischenablage\ndrücke <code>ESC/Abbrechen</code> zum Schliessen",

		"frt_dec": "Kann Fälle von beschädigten Dateien beheben\">url-decode",
		"frt_rst": "Geänderte Dateinamen auf Orginale zurücksetzen\">↺ zurücksetzen",
		"frt_abrt": "Abbrechen und dieses Fenster schliessen\">❌ abbrechen",
		"frb_apply": "ÜBERNEHMEN",
		"fr_adv": "Stapel-/Metadaten-/Musterumbenennung\">erweitert",
		"fr_case": "Groß-/Kleinschreibung beachten (Regex)\">Großschreibung",
		"fr_win": "Windows-kompatible Namen; ersetzt <code>&lt;&gt;:&quot;\\|?*</code> durch japanische Fullwidth-Zeichen\">win",
		"fr_slash": "Ersetzt <code>/</code> durch ein Zeichen, das keine neuen Ordner erstellt\">no /",
		"fr_re": "Regex-Suchmuster für Originaldateinamen; Erfassungsgruppen können im Formatfeld unten als &lt;code&gt;(1)&lt;/code&gt; und &lt;code&gt;(2)&lt;/code&gt; usw. referenziert werden",
		"fr_fmt": "inspiriert von foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; wird durch Songtitel ersetzt,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; überspringt [diesen] Teil falls Interpret leer$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; füllt die Titelnummer auf 2 Ziffern auf",
		"fr_pdel": "Löschen",
		"fr_pnew": "Speichern als",
		"fr_pname": "Gib der Vorlage einen Namen",
		"fr_aborted": "Abgebrochen",
		"fr_lold": "Alter Name",
		"fr_lnew": "Neuer Name",
		"fr_tags": "Tags für die ausgewählten Dateien (liest nur, als Referenz):",
		"fr_busy": "Benenne {0} Elemente um...\n\n{1}",
		"fr_efail": "Umbenennen fehlgeschlagen:\n",
		"fr_nchg": "{0} der neuen Namen wurden angepasst durch <code>win</code> und/oder <code>no /</code>\n\nMöchtest du mit diesen geänderten Namen fortfahren?",

		"fd_ok": "Löschen OK",
		"fd_err": "Löschen fehlgeschlagen:\n",
		"fd_none": "Nichts würde gelöscht; vielleicht durch die Serverkonfiguration blockiert (xbd)?",
		"fd_busy": "Lösche {0} Elemente...\n\n{1}",
		"fd_warn1": "Diese {0} Elemente LÖSCHEN?",
		"fd_warn2": "<b>Ich frage das letzte Mal!</b> Was weg ist, ist weg. Keine Chance, das rückgängig zu machen. Löschen?",

		"fc_ok": "{0} Elemente ausgeschnitten",
		"fc_warn": '{0} Elemente in die Zwischenablage kopiert\n\nAber: nur <b>dieses</b> Browsertab kann sie einfügen\n(da deine Auswahl so abartig riesig war)',

		"fcc_ok": "{0} Elemente in die Zwischenablage kopiert",
		"fcc_warn": '{0} Elemente in die Zwischenablage kopiert\n\nAber: nur <b>dieses</b> Browsertab kann sie einfügen\n(da deine Auswahl so abartig riesig war)',

		"fp_apply": "Diese Namen verwenden",
		"fp_ecut": "Kopiere erst ein paar Dateien / Ordner, um sie einzufügen\n\nTipp: Ausschneiden und Kopieren funktioniert über Browsertabs hinweg",
		"fp_ename": "{0} Elemente konnten nicht verschoben werden, weil bereits andere Dateien mit diesen Namen existieren. Gib ihnen unten neue Namen um fortzufahren, oder lass das Feld leer zum Überspringen:",
		"fcp_ename": "{0} Elemente konnten nicht kopiert werden, weil bereits andere Dateien mit diesen Namen existieren. Gib ihnen unten neue Namen um fortzufahren, oder lass das Feld leer zum Überspringen:",
		"fp_emore": "Es gibt noch ein paar Dateinamen, die geändert werden müssen",
		"fp_ok": "Verschieben OK",
		"fcp_ok": "Kopieren OK",
		"fp_busy": "Verschiebe {0} Elemente...\n\n{1}",
		"fcp_busy": "Kopiere {0} Elemente...\n\n{1}",
		"fp_abrt": "Abbrechen...", //m
		"fp_err": "Verschieben fehlgeschlagen:\n",
		"fcp_err": "Kopieren fehlgeschlagen:\n",
		"fp_confirm": "Diese {0} Elemente hierher verschieben?",
		"fcp_confirm": "Diese {0} Elemente hierher kopieren?",
		"fp_etab": 'Konnte die Zwischenablage nicht vom anderen Browsertab lesen',
		"fp_name": "Lade Datei von deinem Gerät hoch. Gib ihr einen Namen:",
		"fp_both_m": '<h6>Wähle, was eingefügt werden soll</h6><code>Eingabe</code> = {0} Dateien von «{1}» verschieben\n<code>ESC</code> = {2} Dateien von deinem Gerät hochladen',
		"fcp_both_m": '<h6>Wähle, was eingefügt werden soll</h6><code>Eingabe</code> = {0} Dateien von «{1}» kopieren\n<code>ESC</code> = {2} Dateien von deinem Gerät hochladen',
		"fp_both_b": '<a href="#" id="modal-ok">Verschieben</a><a href="#" id="modal-ng">Hochladen</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopieren</a><a href="#" id="modal-ng">Hochladen</a>',

		"mk_noname": "Tipp' mal vorher lieber einen Namen in das Textfeld links, bevor du das machst :p",

		"tv_load": "Textdatei wird geladen:\n\n{0}\n\n{1}% ({2} von {3} MiB geladen)",
		"tv_xe1": "Konnte Textdatei nicht laden:\n\nFehler ",
		"tv_xe2": "404, Datei nicht gefunden",
		"tv_lst": "Liste der Textdateien in",
		"tvt_close": "Zu Ordneransicht zurück$NHotkey: M (oder Esc)\">❌ Schliessen",
		"tvt_dl": "Diese Datei herunterladen$NHotkey: Y\">💾 Herunterladen",
		"tvt_prev": "Vorheriges Dokument zeigen$NHotkey: i\">⬆ vorh.",
		"tvt_next": "Nächstes Dokument zeigen$NHotkey: K\">⬇ nächst.",
		"tvt_sel": "Wählt diese Datei aus &nbsp; ( zum Ausschneiden / Kopieren / Löschen / ... )$NHotkey: S\">ausw.",
		"tvt_edit": "Datei im Texteditor zum Bearbeiten öffnen$NHotkey: E\">✏️ bearb.",
		"tvt_tail": "Datei auf Veränderungen überwachen; Neue Zeilen werden in Echtzeit angezeigt\">📡 folgen",
		"tvt_wrap": "Zeilenumbruch\">↵",
		"tvt_atail": "Automatisch nach unten scrollen\">⚓",
		"tvt_ctail": "Terminal-Farben dekodieren (ANSI Escape Codes)\">🌈",
		"tvt_ntail": "Scrollback limitieren (Menge an Bytes an Text, die geladen bleiben sollen)",

		"m3u_add1": "Song wurde zur M3U-Playlist hinzugefügt",
		"m3u_addn": "{0} Songs zur M3U-Playlist hinzugefügt",
		"m3u_clip": "M3U-Playlist in die Zwischenablage kopiert\n\nDu solltest eine neue Datei mit dem Namen something.m3u erstellen und die Playlist da rein kopieren; damit wird die Playlist abspielbar",

		"gt_vau": "nur Ton abspielen, kein Video zeigen\">🎧",
		"gt_msel": "Dateiauswahl aktivieren; STRG-klicke eine Datei zum überschreiben$N$N&lt;em&gt;wenn aktiv: Datei / Ordner doppelklicken zum Öffnen&lt;/em&gt;$N$NHotkey: S\">multiselect",
		"gt_crop": "Vorschaubilder mittig zuschneiden\">crop",
		"gt_3x": "hochauflösende Vorschaubilder\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "kürzen",
		"gt_sort": "sortieren nach",
		"gt_name": "Name",
		"gt_sz": "Grösse",
		"gt_ts": "Datum",
		"gt_ext": "Typ",
		"gt_c1": "Dateinamen mehr kürzen (weniger zeigen)",
		"gt_c2": "Dateinamen weniger kürzen (mehr zeigen)",

		"sm_w8": "Suche ...",
		"sm_prev": "Die Suchresultate gehören zu einer vorherigen Suchanfrage:\n  ",
		"sl_close": "Suchresultate schliessen",
		"sl_hits": "Zeige {0} Treffer",
		"sl_moar": "Mehr laden",

		"s_sz": "Grösse",
		"s_dt": "Datum",
		"s_rd": "Pfad",
		"s_fn": "Name",
		"s_ta": "Tags",
		"s_ua": "up@",
		"s_ad": "adv.",
		"s_s1": "minimum MiB",
		"s_s2": "maximum MiB",
		"s_d1": "min. iso8601",
		"s_d2": "max. iso8601",
		"s_u1": "hochgeladen nach",
		"s_u2": "und/oder vor",
		"s_r1": "Pfad enthält &nbsp; (Leerzeichen-separiert)",
		"s_f1": "Name enthält &nbsp; (negieren mit -nope)",
		"s_t1": "Tags enthält &nbsp; (^=start, end=$)",
		"s_a1": "spezifische Metadaten-Eigenschaften",

		"md_eshow": "Kann nicht rendern ",
		"md_off": "[📜<em>readme</em>] deaktiviert in [⚙️] -- Dokument versteckt",

		"badreply": "Hab die Antwort vom Server nicht verstanden. (badreply)",

		"xhr403": "403: Zugriff verweigert\n\nVersuche, F5 zu drücken. Vielleicht wurdest du abgemeldet.",
		"xhr0": "Unbekannt (wahrschenlich Verbindung zum Server verloren oder der Server ist offline)",
		"cf_ok": "Sorry dafür -- Der DD" + wah + "oS-Schutz hat angeschlagen.\n\nEs sollte in etwa 30 Sekunden weitergehen.\n\nFalls nichts passiert, drück' F5, um die Seite neuzuladen",
		"tl_xe1": "Konnte Unterordner nicht auflisten:\n\nFehler ",
		"tl_xe2": "404: Ordner nicht gefunden",
		"fl_xe1": "Konnte Dateien in Ordner nicht auflisten:\n\nFehler ",
		"fl_xe2": "404: Ordner nicht gefunden",
		"fd_xe1": "Konnte Unterordner nicht erstellen:\n\nFehler ",
		"fd_xe2": "404: Übergeordneter Ordner nicht gefunden",
		"fsm_xe1": "Konnte Nachricht nicht senden:\n\nFehler ",
		"fsm_xe2": "404: Übergeordneter Ordner nicht gefunden",
		"fu_xe1": "Konnte unpost-Liste nicht laden:\n\nFehler ",
		"fu_xe2": "404: Datei nicht gefunden??",

		"fz_tar": "Unkomprimierte GNU TAR-Datei (Linux / Mac)",
		"fz_pax": "Unkomprimierte pax-format TAR-Datei (etwas langsamer)", //m
		"fz_targz": "GNU-TAR mit gzip Level 3 Kompression$N$Nüblicherweise recht langsam,$Nbenutze stattdessen ein unkomprimiertes TAR",
		"fz_tarxz": "GNU-TAR mit xz level 1 Kompression$N$Nüblicherweise recht langsam,$Nbenutze stattdessen ein unkomprimiertes TAR",
		"fz_zip8": "ZIP mit UTF8-Dateinamen (könnte kaputt gehen auf Windows 7 oder älter)",
		"fz_zipd": "ZIP mit traditionellen CP437-Dateinamen, für richtig alte Software",
		"fz_zipc": "CP437 mit CRC32 früh berechnet,$Nfür MS-DOS PKZIP v2.04g (Oktober 1993)$N(braucht länger zum Verarbeiten, bevor der Download starten kann)",

		"un_m1": "Unten kannst du deine neusten Uploads löschen (oder Unvollständige abbrechen)",
		"un_upd": "Neu laden",
		"un_m4": "Oder die unten sichtbaren Dateien teilen:",
		"un_ulist": "Anzeigen",
		"un_ucopy": "Kopieren",
		"un_flt": "Optionale Filter:&nbsp; URL muss enthalten",
		"un_fclr": "Filter löschen",
		"un_derr": 'unpost-delete fehlgeschlagen:\n',
		"un_f5": 'Etwas ist kaputt gegangen, versuche die Seite neuzuladen (drücke dazu F5)',
		"un_uf5": "Sorry, aber du musst die Seite neuladen (z.B. in dem du F5 oder STRG-R drückst) bevor zu diesen Upload abbrechen kannst",
		"un_nou": '<b>Warnung:</b> Der Server ist grade zu beschäftigt, um unvollständige Uploads anzuzeigen; Drücke den "Neu laden"-Link in ein paar Sekunden',
		"un_noc": '<b>Warnung:</b> unpost von vollständig hochgeladenen Dateien ist über die Serverkonfiguration gesperrt',
		"un_max": "Zeige die ersten 2000 Dateien (benutze Filter, um die gewünschten Dateien zu finden)",
		"un_avail": "{0} zuletzt hochgeladene Dateien können gelöscht werden<br />{1} Unvollständige können abgebrochen werden",
		"un_m2": "Sortiert nach Upload-Zeitpunkt; neuste zuerst:",
		"un_no1": "Hoppala! Es gibt keine ausreichend aktuellen Uploads.",
		"un_no2": "Pech gehabt! Kein Upload, der zu dem Filter passen würde, ist neu genug",
		"un_next": "Lösche die nächsten {0} Dateien",
		"un_abrt": "Abbrechen",
		"un_del": "Löschen",
		"un_m3": "Deine letzten Uploads werden geladen ...",
		"un_busy": "Lösche {0} Dateien ...",
		"un_clip": "{0} Links in die Zwischenablage kopiert",

		"u_https1": "für bessere Performance solltest du",
		"u_https2": "auf HTTPS wechseln",
		"u_https3": " ",
		"u_ancient": 'Dein Browser ist verdammt antik -- vielleicht solltest du <a href="#" onclick="goto(\'bup\')">stattdessen bup benutzen</a>',
		"u_nowork": "Benötigt Firefox 53+ oder Chrome 57+ oder iOS 11+",
		"tail_2old": "Benötigt Firefox 105+ oder Chrome 71+ oder iOS 14.5+",
		"u_nodrop": 'Dein Browser ist zu alt für Drag-and-Drop Uploads',
		"u_notdir": "Das ist kein Ordner!\n\nDein Browser ist zu alt,\nversuch stattdessen dragdrop",
		"u_uri": "Um Bilder per Drag-and-Drop aus anderen Browserfenstern hochzuladen,\nlass' sie bitte über dem grossen Upload-Button fallen",
		"u_enpot": 'Zu <a href="#">Potato UI</a> wechseln (kann Upload-Geschw. verbessern)',
		"u_depot": 'Zu <a href="#">fancy UI</a> wechseln (kann Upload-Geschw. verschlechtern)',
		"u_gotpot": 'Wechsle zu Potato UI für verbesserte Upload-Geschwindigkeit,\n\nwenn du anderer Meinung bist, kannst du gerne zurück wechseln',
		"u_pott": "<p>Dateien: &nbsp; <b>{0}</b> fertig, &nbsp; <b>{1}</b> fehlgeschlagen, &nbsp; <b>{2}</b> in Bearbeitung, &nbsp; <b>{3}</b> ausstehend</p>",
		"u_ever": "Dies ist der Basic Uploader; up2k benötigt mind. <br>Chrome 21 // Firefox 13 // Edge 12 // Opera 12 // Safari 5.1",
		"u_su2k": 'Dies ist der Basic Uploader; <a href="#" id="u2yea">up2k</a> ist besser',
		"u_uput": 'Für Geschwindigkeit optimieren (Checksum überspringen)',
		"u_ewrite": 'Du hast kein Schreibzugriff auf diesen Ordner',
		"u_eread": 'Du hast kein Lesezugriff auf diesen Ordner',
		"u_enoi": 'file-search ist in der Serverkonfiguration nicht aktiviert',
		"u_enoow": "Überschreiben wird hier nicht funktionieren; benötige Lösch-Berechtigung",
		"u_badf": 'Diese {0} Dateien (von insgesammt {1}) wurden übersprungen, wahrscheinlich wegen Dateisystem-Berechtigungen:\n\n',
		"u_blankf": 'Diese {0} Dateien (von insgesammt {1}) sind leer; trotzdem hochladen?\n\n',
		"u_applef": 'Diese {0} Dateien (von insgesammt {1}) sind möglicherweise unerwünscht;\n<code>OK/Eingabe</code> drücken, um die folgenden Dateien zu überspringen.\nDrücke <code>Abbrechen/ESC</code> um sie NICHT zu überspringen und diese AUCH HOCHZULADEN:\n\n',
		"u_just1": '\nFunktioniert vielleicht besser, wenn du nur eine Datei auswählst',
		"u_ff_many": "Falls du <b>Linux / MacOS / Android</b> benutzt, <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>könnte</em> Firefox mit dieser Menge an Dateien crashen!</a>\nFalls das passiert, probier nochmal (oder benutz Chrome).",
		"u_up_life": "Dieser Upload wird vom Server gelöscht\n{0} nachdem er abgeschlossen ist",
		"u_asku": 'Diese {0} Dateien nach <code>{1}</code> hochladen',
		"u_unpt": "Du kannst diesen Upload rückgängig machen mit dem 🧯 oben-links",
		"u_bigtab": 'Versuche {0} Dateien anzuzeigen.\n\nDas könnte dein Browser crashen, bist du dir wirklich sicher?',
		"u_scan": 'Scanne Dateien...',
		"u_dirstuck": 'Ordner-Iterator blieb hängen beim Versuch, diese {0} Einträge zu lesen; überspringe:',
		"u_etadone": 'Fertig ({0}, {1} Dateien)',
		"u_etaprep": '(Upload wird vorbereitet)',
		"u_hashdone": 'Hashing vollständig',
		"u_hashing": 'Hash',
		"u_hs": 'Wir schütteln uns die Hände ("handshaking")...',
		"u_started": "Dateien werden hochgeladen; siehe [🚀]",
		"u_dupdefer": "Duplikat; wird nach allen anderen Dateien verarbeitet",
		"u_actx": "Klicke diesen Text um Performance-<br />Einbusen zu Vermeiden beim Wechsel auf andere Fenster/Tabs",
		"u_fixed": "OK!&nbsp; Habs repariert 👍",
		"u_cuerr": "failed to upload chunk {0} of {1};\nprobably harmless, continuing\n\nfile: {2}",
		"u_cuerr2": "server rejected upload (chunk {0} of {1});\nwill retry later\n\nfile: {2}\n\nerror ",
		"u_ehstmp": "versuche nochmal; siehe unten-rechts",
		"u_ehsfin": "Der Server hat die Anfrage zum Abschluss des Uploads abgelehnt; versuche nochmal...",
		"u_ehssrch": "Der Server hat die Anfrage zur Suche abgelehnt; versuche nochmal...",
		"u_ehsinit": "Der Server hat die Anfrage zum Start des Uploads abgelehnt; versuche nochmal...",
		"u_eneths": "Netzwerkfehler beim Upload-Handshake; versuche nochmal...",
		"u_enethd": "Netzwerkfehler beim Testen der Existenz des Ziels; versuche nochmal...",
		"u_cbusy": "Der Server mag uns grade nicht mehr nach einem Netzwerkglitch, warte einen Moment...",
		"u_ehsdf": "Server hat kein Speicherplatz mehr!\n\nwerde es erneut versuchen, falls jemand\ngenug Platz schafft um fortzufahren",
		"u_emtleak1": "scheint, als ob dein Browser ein Memory Leak hätte;\nbitte",
		"u_emtleak2": ' <a href="{0}">wechsle auf HTTPS (empfohlen)</a> oder ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'versuche folgendes:\n<ul><li>drücke <code>F5</code> um die Seite neu zu laden</li><li>deaktivere dann den &nbsp;<code>mt</code>&nbsp; Button in den &nbsp;<code>⚙️ Einstellungen</code></li><li>und versuche den Upload nochmal.</li></ul>Uploads werden etwas langsamer sein, aber man kann ja nicht alles haben.\nSorry für die Umstände !\n\nPS: Chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">hat ein Bugfix</a> dafür',
		"u_emtleakf": 'versuche folgendes:\n<ul><li>drücke <code>F5</code> um die Seite neu zu laden</li><li>aktivere dann <code>🥔</code> (potato) im Upload UI<li>und versuche den Upload nochmal</li></ul>\nPS: Firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">hat hoffentlich irgendwann ein Bugfix</a>',
		"u_s404": "nicht auf dem Server gefunden",
		"u_expl": "erklären",
		"u_maxconn": "die meisten Browser limitieren dies auf 6, aber Firefox lässt mehr zu unter <code>connections-per-server</code> in <code>about:config</code>",
		"u_tu": '<p class="warn">WARNUNG: Turbo aktiviert, <span>&nbsp;Client könnte unvollständige Uploads verpassen und nicht wiederholen; siehe Turbo-Button Tooltip</span></p>',
		"u_ts": '<p class="warn">WARNUNG: Turbo aktiviert, <span>&nbsp;Suchresultate können inkorrekt sein; siehe Turbo-Button Tooltip</span></p>',
		"u_turbo_c": "Turbo deaktiviert in der Serverkonfiguration",
		"u_turbo_g": "Turbo deaktiviert, da du keine Listen-Berechtigung\nauf diesem Volume hast",
		"u_life_cfg": 'Autodelete nach <input id="lifem" p="60" /> min (or <input id="lifeh" p="3600" /> h)',
		"u_life_est": 'Upload wird gelöscht <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'Dieser Ordner erzwingt eine\nmax Lebensdauer von {0}',
		"u_unp_ok": 'unpost ist erlaubt für {0}',
		"u_unp_ng": 'unpost wird NICHT erlaubt',
		"ue_ro": 'Du hast nur Lese-Zugriff auf diesen Ordner\n\n',
		"ue_nl": 'Du bist nicht angemeldet',
		"ue_la": 'Du bist angemeldet als "{0}"',
		"ue_sr": 'Du bist derzeit im Suchmodus\n\nWechsle zum Upload-Modus indem du auf die Lupe 🔎 klickst (neben dem grossen SUCHEN Button), und versuche den Upload nochmal.\n\nSorry',
		"ue_ta": 'Versuche den Upload nochmal, sollte jetzt klappen',
		"ue_ab": "Diese Datei wird gerade in einem anderen Ordner hochgeladen, dieser Upload muss zuerst abgeschlossen werden, bevor die Datei woanders hochgeladen werden kann.\n\nDu kannst den Upload abbrechen und vergessen mit dem 🧯 oben-links",
		"ur_1uo": "OK: Datei erfolgreich hochgeladen",
		"ur_auo": "OK: Alle {0} Dateien erfolgreich hochgeladen",
		"ur_1so": "OK: Datei auf dem Server gefunden",
		"ur_aso": "OK: Alle {0} Dateien auf dem Server gefunden",
		"ur_1un": "Upload fehlgeschlagen, sorry",
		"ur_aun": "Alle {0} Uploads fehlgeschlagen, sorry",
		"ur_1sn": "Datei wurde NICHT auf dem Server gefunden",
		"ur_asn": "Die {0} Dateien wurden NICHT auf dem Server gefunden",
		"ur_um": "Fertig;\n{0} Uploads OK,\n{1} Uploads fehlgeschlagen, sorry",
		"ur_sm": "Fertig;\n{0} Uploads gefunden auf dem Server,\n{1} Dateien NICHT gefunden auf dem Server",

		"lang_set": "Neuladen um Änderungen anzuwenden?",
	},
	"epo": {
		"tt": "Esperanto",

		"cols": {
			"c": "ago-butonoj",
			"dur": "daŭro",
			"q": "kvalito / bitrapido",
			"Ac": "sonkodeko",
			"Vc": "videokodeko",
			"Fmt": "formato / ujo",
			"Ahash": "kontrolsumo de aŭdio",
			"Vhash": "kontrolsumo de video",
			"Res": "distingivo",
			"T": "dosiertipo",
			"aq": "kvalito / bitrapido de aŭdio",
			"vq": "kvalito / bitrapido de video",
			"pixfmt": "specimenado / strukturo de bilderoj",
			"resw": "horizontala distingivo",
			"resh": "vertikala distingivo",
			"chs": "nombro de aŭdio-kanaloj",
			"hz": "sonpecrapido"
		},

		"hks": [
			[
				"misc",
				["ESK", "malfermi variajn aferojn"],

				"file-manager",
				["G", "baskuli inter lista kaj krada vido"],
				["T", "baskuli montradon de bildetoj"],
				["⇧ A/D", "grandeco de bildetoj"],
				["stir-K", "forigi elektitajn"],
				["stir-X", "eltondi elektaĵon al tondujo"],
				["stir-C", "kopii elektaĵon al tondujo"],
				["stir-V", "alglui (movi/kopii) ĉi tien"],
				["Y", "elŝuti elektitajn"],
				["F2", "alinomi elektitajn"],

				"file-list-sel",
				["spacoklavo", "baskuli elektadon de dosieroj"],
				["↑/↓", "movi elektado-kursoron"],
				["stir ↑/↓", "movi kursoron kaj vidujon"],
				["⇧ ↑/↓", "elekti (mal)sekvan dosieron"],
				["stir-A", "elekti ĉiujn dosier(uj)ojn"],
			], [
				"navigation",
				["B", "baskuli inter paĝnivela kaj arbovida navigo"],
				["I/K", "(mal-)sekva dosierujo"],
				["M", "parent folder (or unexpand current)"],
				["V", "baskuli inter montrado de dosierujoj aŭ tekst-dosieroj en toggle folders / textfiles en arbovida navig-panelo"],
				["A/D", "grandeco de arbovida navig-panelo"],
			], [
				"audio-player",
				["J/L", "(mal-)sekva kanto"],
				["U/O", "iri 10 sekundoj (mal)antaŭen"],
				["0..9", "iri al 0%..90%"],
				["P", "ludi/paŭzigi (ankaŭ komencas)"],
				["S", "elekti ludantan kanton"],
				["Y", "elŝuti kanton"],
			], [
				"image-viewer",
				["J/L, ←/→", "(mal)sekva bildo"],
				["Home/End", "unua/lasta bildo"],
				["F", "plenekrana vido"],
				["R", "turni dekstrumen"],
				["⇧ R", "turni maldekstrumen"],
				["S", "elekti bildon"],
				["Y", "elŝuti bildon"],
			], [
				"video-player",
				["U/O", "iri 10 sekundoj (mal)antaŭen"],
				["P/K/Spaco", "ludi/paŭzigi"],
				["C", "??continue playing next"],
				["V", "cikla ludado"],
				["M", "silentigi"],
				["[ and ]", "agordi intervalon de cikla ludado"],
			], [
				"textfile-viewer",
				["I/K", "(mal)sekva dosiero"],
				["M", "fermi dosieron"],
				["E", "redakti dosieron"],
				["S", "elekti dosieron (por eltondado/kopiado/alinomado)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Rezigni",

		"enable": "Ŝalti",
		"danger": "DANĜERO",
		"clipped": "kopiita al tondujo",

		"ht_s1": "sekundo",
		"ht_s2": "sekundoj",
		"ht_m1": "minuto",
		"ht_m2": "minutoj",
		"ht_h1": "horo",
		"ht_h2": "horoj",
		"ht_d1": "tago",
		"ht_d2": "tagoj",
		"ht_and": " kaj ",

		"goh": "stirpanelo",
		"gop": 'malsekva dosierujo">malsekva',
		"gou": 'supra dosierujo">supren',
		"gon": 'sekva dosierujo">sekva',
		"logout": "Adiaŭi kiel ",
		"login": "Ensaluti",
		"access": " atingo",
		"ot_close": "fermi submenuon",
		"ot_search": "serĉi dosierojn per atributoj, indiko / nomo, etikedoj de muziko aŭ ĉiu kombinaĵo de tiuj parametroj$N$N&lt;code&gt;foo bar&lt;/code&gt; = devas enhavi ambaŭ «foo» kaj «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = devas enhavi «foo», sed ne «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = komenci per «yana» kaj esti dosieron de formato «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = enhavi precipe «try unite»$N$Nformato de datoj estas iso-8601, ekzemple$N&lt;code&gt;2009-12-31&lt;/code&gt; aŭ &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: forigi viaj plej lastaj alŝutoj, aŭ ĉesigi nefinigitajn",
		"ot_bup": "bup: fundamenta alŝutilo, funkias eĉ kun netscape 4.0",
		"ot_mkdir": "mkdir: krei novan dosierujon",
		"ot_md": "new-md: krei novan markdown-dosieron",
		"ot_msg": "msg: sendi mesaĝon al servila protokolo",
		"ot_mp": "agordoj de medialudilo",
		"ot_cfg": "aliaj agordoj",
		"ot_u2i": 'up2k: alŝuti dosierojn (se vi havas skribo-atingon) aŭ ŝalti ŝerc-reĝimon por determini, ĉu dosieroj jam ekzistas ie ĉe la servilo$N$Nalŝutoj estas daŭrigeblaj, plurfadenaj, kaj prezervas tempindikojn, sed ĝi estas pli procesor-intensa ol [🎈]&nbsp; (la fundamenta alŝutilo)<br /><br />dum alŝutado, ĉi tiu simbolo iĝas plenumindikilo!',
		"ot_u2w": 'up2k: alŝuti dosierojn kun subteno de daŭrigeblo (fermu vian retumilon kaj demetu la samajn dosierojn poste)$N$Nalŝutoj estas daŭrigeblaj, plurfadenaj, kaj prezervas tempindikojn, sed ĝi estas pli procesor-intensa ol [🎈]&nbsp; (la fundamenta alŝutilo)<br /><br />dum alŝutado, ĉi tiu simbolo iĝas plenumindikilo!',
		"ot_noie": 'Bonvolu uzi retumilojn Chrome / Firefox / Edge',

		"ab_mkdir": "krei dosierujon",
		"ab_mkdoc": "krei markdown-dosieron",
		"ab_msg": "sendi mesaĝon al protokolo",

		"ay_path": "iri al dosierujoj",
		"ay_files": "iri al dosieroj",

		"wt_ren": "alinomi elektitajn aĵojn$NFulmoklavo: F2",
		"wt_del": "forigi elektitajn aĵojn$NFulmoklavo: stir-K",
		"wt_cut": "eltondi elektitajn aĵojn &lt;small&gt;(do alglui ien aliloke)&lt;/small&gt;$NFulmoklavo: stir-X",
		"wt_cpy": "kopii elektitajn aĵojn al tondujo$N(por alglui ien aliloke)$NFulmoklavo: stir-C",
		"wt_pst": "alglui antaŭe eltonditajn / kopiitajn aĵojn$NFulmoklavo: stir-V",
		"wt_selall": "elekti ĉiujn dosierojn$NFulmoklavo: stir-A (se dosiero estas elektita)",
		"wt_selinv": "inversigi elektaĵon",
		"wt_zip1": "elŝuti dosierujon kiel arkivo",
		"wt_selzip": "elŝuti elektaĵon kiel arkivo",
		"wt_seldl": "elŝuti elektaĵon kiel apartaj dosieroj$NFulmoklavo: Y",
		"wt_npirc": "kopii IRC-formatan muzikaĵ-informon",
		"wt_nptxt": "kopii tekstan muzikaĵ-informon",
		"wt_m3ua": "aldoni al m3u-ludliston (klaku butonon <code>📻copy</code> poste)",
		"wt_m3uc": "kopii m3u-ludliston al tondujo",
		"wt_grid": "baskuli kradan / listan vidon$NFulmoklavo: G",
		"wt_prev": "malsekva muzikaĵo$NFulmoklavo: J",
		"wt_play": "ludi / paŭzigi$NFulmoklavo: P",
		"wt_next": "sekva muzikaĵo$NFulmoklavo: L",

		"ul_par": "paralelaj alŝutoj:",
		"ut_rand": "hazardigi dosiernomojn",
		"ut_u2ts": "kopii la tempon de lasta modifo$Nel via dosiersistemo al la servilo\">📅",
		"ut_ow": "ĉu anstataŭigi dosierojn ĉe la servilo?$N🛡️: neniam (dosiero estos alŝutita kun nova dosiernomo)$N🕒: anstataŭigi, se servila dosiero estas pli malnova ol via$N♻️: ĉiam anstataŭigi, se dosieroj estas malsamaj",
		"ut_mt": "daŭri kalkuladon de kontrolsumoj por aliaj dosieroj dum alŝutado$N$Nmalŝaltinda, se via procesoro aŭ disko ne estas sufiĉe rapidaj",
		"ut_ask": 'peti konfirmon antaŭ komenco de alŝutado">💭',
		"ut_pot": "plirapidigi alŝutadon por malrapidaj komputiloj$Nper malkomplikado de fasado",
		"ut_srch": "ne alŝuti ion ajn, nur kontroli, ke la dosieroj $N jam ekzistas ĉe la servilo (ĉiuj dosierujoj, kiuj vi povas legi, estos skanitaj)",
		"ut_par": "paŭzi alŝutadon per agordado kiel 0$N$Npligrandigi, se via konekto estas malrapida aŭ malfruema$N$Nagordi kiel 1, se la loka reto aŭ servila disko ne estas sufiĉe rapidaj",
		"ul_btn": "demeti dosier(uj)ojn<br>ĉi tien (aŭ alklaki ĉi tien)",
		"ul_btnu": "A L Ŝ U T I",
		"ul_btns": "S E R Ĉ I",

		"ul_hash": "k-sumado",
		"ul_send": "sendado",
		"ul_done": "finita",
		"ul_idle1": "neniuj alŝutoj envicigitaj",
		"ut_etah": "meza rapido de &lt;em&gt;kontrolsumado&lt;/em&gt;, kaj pritaksita tempo ĝis la fino",
		"ut_etau": "meza rapido de &lt;em&gt;alŝutado&lt;/em&gt;, kaj pritaksita tempo ĝis la fino",
		"ut_etat": "meza &lt;em&gt;tuta&lt;/em&gt; rapido, kaj pritaksita tempo ĝis la fino",

		"uct_ok": "sukcese plenumita",
		"uct_ng": "malbona: malsukceso / malakcepto / ne trovita (no good)",
		"uct_done": "ambaŭ ok kaj ng",
		"uct_bz": "kontrolsumado aŭ alŝutado (busy)",
		"uct_q": "envicigita (queue)",

		"utl_name": "dosiernomo",
		"utl_ulist": "listigi",
		"utl_ucopy": "kopii",
		"utl_links": "ligilojn",
		"utl_stat": "stato",
		"utl_prog": "progreso",

		// keep short:
		"utl_404": "404",
		"utl_err": "ERARO",
		"utl_oserr": "OS-eraro",
		"utl_found": "trovita",
		"utl_defer": "postigita",
		"utl_yolo": "rapidega",
		"utl_done": "finita",

		"ul_flagblk": "la dosieroj estis aldonita al la vico,</b><br>sed alia langeto de retumilo jam alŝutas dosierojn per up2k,<br>do tiu alŝutado devas finiĝi unue",
		"ul_btnlk": "la agordado de servilo ne permesas ŝanĝi tiun agordon",

		"udt_up": "Alŝuti",
		"udt_srch": "Serĉi",
		"udt_drop": "demetu ĉi tien",

		"u_nav_m": '<h6>do, kion vi havas ĉi tie?</h6><code>Enter</code> = Dosierojn (unu al multaj)\n<code>ESK</code> = Unu dosierujon (eble kun subdosierujoj)',
		"u_nav_b": '<a href="#" id="modal-ok">Dosierojn</a><a href="#" id="modal-ng">Unu dosierujo</a>',

		"cl_opts": "ŝaltiloj",
		"cl_themes": "etoso",
		"cl_langs": "lingvo",
		"cl_ziptype": "elŝutado de dosieroj",
		"cl_uopts": "agordoj de up2k",
		"cl_favico": "retpaĝsimbolo",
		"cl_bigdir": "grandaj ujoj",
		"cl_hsort": "#ordigo",
		"cl_keytype": "skemo de fulmoklavoj",
		"cl_hiddenc": "kaŝitaj kolumnoj",
		"cl_hidec": "kaŝi",
		"cl_reset": "restarigi",
		"cl_hpick": "alklaki la kapojn de kolumnoj por kasi en la suban tabelon",
		"cl_hcancel": "kaŝado de kolumno nuligita",

		"ct_grid": '田 krado',
		"ct_ttips": '◔ ◡ ◔">ℹ️ ŝpruchelpiloj',
		"ct_thumb": 'dum krado-vido, baskuli montradon de simboloj aŭ bildetoj$NFulmoklavo: T">🖼️ bildetoj',
		"ct_csel": 'uzi STIR kaj MAJ por elekti dosierojn en krado-vido">elekto',
		"ct_ihop": 'montri la lastan viditan bildo-dosieron post fermado de bildo-vidilo">g⮯',
		"ct_dots": 'montri kaŝitajn dosierojn (se servilo permesas)">kaŝitaj',
		"ct_qdel": 'peti konfirmon nur unufoje antaŭ forigado">rapid-forig.',
		"ct_dir1st": 'ordigi dosierujojn antaŭ dosieroj">📁 unue',
		"ct_nsort": 'numera ordigo de dosiernomoj (ekz. &lt;code&gt;2&lt;/code&gt; antaŭ &lt;code&gt;11&lt;/code&gt;)">№.ord',
		"ct_utc": 'montri ĉiuj datoj kaj tempoj per UTC">UTC',
		"ct_readme": 'montri enhavon de README.md en listaĵo de dosieroj">📜 readme',
		"ct_idxh": 'montri paĝon index.html anstataŭ listaĵo de dosieroj">htm',
		"ct_sbars": 'montri rulumskalojn">⟊',

		"cut_umod": "se dosiero jam ekzistas en la servilo, ŝanĝi la tempon de lasta modifo laŭ via dosiero (bezonas permesojn write+delete)\">re📅igi",

		"cut_turbo": "rapidigi alŝutojn KOSTE DE TUTA KONTROLADO:$N$Nuzinda, se vi alŝutis grandegajn dosierojn, devis haltigi la alŝutadon, kaj nun volas daŭrigi ĝin rapidege$N$Nse ĉi tiu agordo estas ŝaltita, anstataŭ kontrolsumado, la servilo nur kontrolas, ĉu la grando de via kaj servila dosieroj estas samaj, kaj ne realŝutas dosierojn kun samaj grandoj$N$Npost ĉio finiĝis, vi devus malŝalti ĉi tiun agordon, do provi &quot;alŝuti&quot; la tiuj samaj dosieroj — la kontrolsumado rekomencos kaj ne realŝutos ion ajn, se la alŝutado vere sukcesis\">rapidega",

		"cut_datechk": "efektas nur se &quot;rapidega&quot; alŝutado estas ŝaltita$N$Nete plibonigas fidindon de kontrolado, per kontrolado de modifo-tempoj aldone al grandoj$N$N<em>teorie</em> estas sufiĉe por detekti nefinigitajn aŭ difektitajn alŝutojn, sed ne estas kompleta alternativo por sen-&quot;rapidega&quot; kontrolado\">dato-kontrolo",

		"cut_u2sz": "grando (en MiBoj) de ĉiu alŝutanta ero; grandaj valoroj estas pli bonaj por longdistancaj konektoj, malgrandajn por malalt-kvalitaj konektoj",

		"cut_flag": "certigi, ke nur unu langeto alŝutas samttempe $N -- aliaj langetoj devas ankaŭ ŝalti ĉi tiun agordon $N -- nur funkcias por langetoj de sama domajno",

		"cut_az": "alŝuti dosierojn en alfabeta ordigo anstataŭ &quot;plej malgrandaj unue&quot;$N$Nalfabeta ordo igas pli simple vidi, ke okazis eraroj en la servilo, sed estas pli malrapida sur tre rapidaj konektoj (ekz. en la loka reto aŭ per fibrooptiko)",

		"cut_nag": "sciigi per operaciumo je fino de alŝutado$N(nur se ĉi tiu langeto de retumilo ne estas aktiva)",
		"cut_sfx": "sciigi per sono je fino de alŝutado$N(nur se ĉi tiu langeto de retumilo ne estas aktiva)",

		"cut_mt": "kontrolsumi dosierojn pli rapide per multaj fadenoj$N$Nuzas teknologio Web Worker, bezonas pli da labormemoro (maksimume 512 MiB)$N$Nplirapidigas https je 30%, http je 4.5x\">mf",

		"cut_wasm": "uzi WASM-modulon anstataŭ kontrolsumilaj funkcioj de retumilo; plirapidigas kontrolsumadon sur Chrome-bazitaj retumiloj, sed ankaŭ pli procesor-intensa; malnovaj versioj de Chrome havas difektojn, kiuj misuzas la tutan labormemoron kaj kraŝas la retumilon, se ĉi tiu agordo estas ŝaltita\">wasm",

		"cft_text": "teksto de retpaĝsimbolo (blankigu kaj reŝargu la paĝon por malŝalti)",
		"cft_fg": "teksta koloro",
		"cft_bg": "fona koloro",

		"cdt_lim": "maks. nombro de dosieroj por montri en dosierujo",
		"cdt_ask": "je malsupro de paĝo, peti por ago$Nanstataŭ ŝarĝi pli da dosieroj",
		"cdt_hsort": "kiom da ordigo-reguloj (&lt;code&gt;,sorthref&lt;/code&gt;) inkludi en adreso de la paĝo. Se agordita kiel 0, reguloj, inkluditaj en la adreso, estos ignoritaj",

		"tt_entree": "montri arbovidan navig-panelon$NFulmoklavo: B",
		"tt_detree": "montri paĝnivelan navig-panelon$NFulmoklavo: B",
		"tt_visdir": "rulumi al elektita dosierujo",
		"tt_ftree": "baskuli dosieruj-arban aŭ teksto-dosieran vidon$NFulmoklavo: V",
		"tt_pdock": "fiksi patrajn dosierojn sur supro de panelo",
		"tt_dynt": "aŭtomate pligrandigi panelon",
		"tt_wrap": "linifaldo",
		"tt_hover": "montri kompletajn nomojn sur musumo$N( paneas rulumadon, se la kursoro de muso $N&nbsp; ne estas en la maldekstra malplenaĵo )",

		"ml_pmode": "je la fino de dosierujo...",
		"ml_btns": "komandoj",
		"ml_tcode": "transkodi",
		"ml_tcode2": "transkodi al",
		"ml_tint": "kolorado",
		"ml_eq": "ekvalizilo",
		"ml_drc": "kompresoro",

		"mt_loop": "ripeti unu kanton\">🔁",
		"mt_one": "haltigi post unu kanto\">1️⃣",
		"mt_shuf": "ludi ĉiu dosierujo en hazarda ordo\">🔀",
		"mt_aplay": "ludi aŭtomate, se ligilo enhavas identigilon de kanto$N$Nmalŝaltado de ĉi tiu agordo ankaŭ malŝaltas ĝisdatigadon de paĝ-adreso, por ke ludado ne rekomenciĝas, se la paĝo estos poste malfermita sen aliaj agordoj\">a▶",
		"mt_preload": "komenci ŝargadon de sekva kanto antaŭ la fino de la nuna, por kontinua ludado\">antaŭŝarg.",
		"mt_prescan": "eniri la sekvan dosierujon antaŭ la fino de la lasta kanto, $Npor ke la retumilo ne interrompis la ludadon\">nav",
		"mt_fullpre": "antaŭŝargi la tutan kanton;$N✅ ŝalti por <b>malaltkvalitaj</b> konektoj,$N❌ eble <b>malŝalti</b> por malrapidaj konektoj\">full",
		"mt_fau": "por poŝtelefonoj: komenci sekvan kanton, eĉ se ĝi ne estis tute ŝargita (povas difektigi la montradon de muzikaĵ-etikedoj)\">☕️",
		"mt_waves": "bildigo:$Nmontri amplitudon de ludanta kanto en ludadbreto\">~",
		"mt_npclip": "montri butonojn por kopiado de ludanta kanto\">/np",
		"mt_m3u_c": "montri butonojn por kopiado de elektitaj kantoj kiel m3u8-ludlisto\">📻",
		"mt_octl": "integrado kun operaciumo (medio-klavoj kaj montriloj)\">integr.",
		"mt_oseek": "movi tra kanto per operaciumaj stiriloj$N$Nnoto: en iuj komputiloj  (iPhone),$N ĉi tiu agordo anstataŭigas la butonon de sekva kanto\">movado",
		"mt_oscv": "montri album-bildojn en montriloj\">bildo",
		"mt_follow": "rulumi la pagon, por ke la ludanta kanto restas videbla\">🎯",
		"mt_compact": "kompaktaj ruliloj\">⟎",
		"mt_uncache": "malplenigi kaŝmemoron &nbsp;(uzinda, se via retumilo kaŝmemoris$Ndifektitan kopion de kanto, kaj ne povas ludi ĝin)\">🗑️ kaŝmem.",
		"mt_mloop": "ripeti la nunan dosierujon\">🔁 ripeti",
		"mt_mnext": "ŝargi la sekvan dosierujon kaj daŭrigi\">📂 sekva",
		"mt_mstop": "haltigi ludadon\">⏸ haltigi",
		"mt_cflac": "konverti el flac / wav al {0}\">flac",
		"mt_caac": "konverti el aac / m4a al {0}\">aac",
		"mt_coth": "konverti aliajn (krom mp3) al {0}\">aliaj",
		"mt_c2opus": "pli bona elekto por propraj komputiloj kaj Android\">opus",
		"mt_c2owa": "opus-weba, por iOS 17.5 kaj pli novaj\">owa",
		"mt_c2caf": "opus-caf, por iOS 11-17\">caf",
		"mt_c2mp3": "por tre malnovaj iloj\">mp3",
		"mt_c2flac": "plej bona sonkvalito, sed grandegaj elŝutoj\">flac",
		"mt_c2wav": "sendensigita ludado (pli bonaj elŝutoj)\">wav",
		"mt_c2ok": "bona elekto",
		"mt_c2nd": "ĉi tiu formato ne estas rekomendita por via aparato, sed ĝi ankaŭ funkcios",
		"mt_c2ng": "via aparato ŝajne ne subtenas ĉi tiun formaton, sed ni provu uzi ĝin malgraŭe",
		"mt_xowa": "estas difektoj en iOS, kiuj preventas fonan ludadon per ĉi tiu formato; bonvolu uzi caf aŭ mp3 anstataŭe",
		"mt_tint": "travideblo (0-100) de ludadbreto$Nvi povas ŝanĝi ĝin, se ĝi aspektas tro distre dum ŝargado",
		"mt_eq": "ŝaltas ekvalizilon kaj stirilon de plifortigado;$N$Nboost (plifortigado) &lt;code&gt;0&lt;/code&gt; = senmodifa 100%a laŭteco$N$Nwidth (larĝo) &lt;code&gt;1 &nbsp;&lt;/code&gt; = senmodifa dukanala sono$Nwidth (larĝo) &lt;code&gt;0.5&lt;/code&gt; = 50% miksado inter maldekstra kaj dekstra kanaloj$Nwidth (larĝo) &lt;code&gt;0 &nbsp;&lt;/code&gt; = unukanala sono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = senvokigo :^)$N$Nŝaltita ekvalizilo ankaŭ forigas paŭzojn inter muzikaĵoj en senpaŭzaj albumoj, agordi ĉion kiel 0 (sed 'width' kiel 1), se vi volas nur tion",
		"mt_drc": "ŝaltas kompresoron de dinamiko (glatigas laŭtecon de muzikaĵoj); ankaŭ ŝaltas ekvalizilon, do agordu ĉion (sed 'width') kiel 0, se vi ne volas ĝin; $N$Nplimalgrandigas laŭtecon de aŭdio super sojlo-valoro ('tresh') da dB; ĉiu proporcio-valoro ('ratio') da dB post 'tresh' 1 dB estos eligita, do implicitaj valoroj (tresh = -24, ratio = 12) faras, ke laŭteco neniam pli grandas ol -22 dB; tiel estas sendanĝera agordi 'boost'on kiel 0.8 aŭ eĉ 1.8 dum ATK = 0 kaj grandega RLS, kiel 90 (funkcias nur en Firefox, RLS estas maksimume 1 en aliaj retumiloj)$N$N(rigardu vikipedion, ĝi klariĝas pli bone)",

		"mb_play": "ludi",
		"mm_hashplay": "ludi ĉi tiun aŭdiodosieron?",
		"mm_m3u": "premu <code>Enter/OK</code> por ludado \npremu <code>ESK/Rezigni</code> por redaktado",
		"mp_breq": "bezonas Firefox 82+, Chrome 73+ aŭ iOS 15+",
		"mm_bload": "ŝargado...",
		"mm_bconv": "konvertado al formato {0}, bonvolu atendi...",
		"mm_opusen": "via retumilo ne povas ludi dosierojn de formatoj aac / m4a;\ntranskodado al opus estas ŝaltigita",
		"mm_playerr": "ludado malsukcesis: ",
		"mm_eabrt": "Klopodo de ludado estis nuligita",
		"mm_enet": "Via retkonekto estas nestabila",
		"mm_edec": "Ĉi tiu dosiero estas ŝajne difektita??",
		"mm_esupp": "Via retumilo ne komprenas ĉi tiun aŭdio-formaton",
		"mm_eunk": "Nekonata eraro",
		"mm_e404": "Ne povas ludi aŭdiaĵon; eraro 404: Dosiero ne trovita.",
		"mm_e403": "Ne povas ludi aŭdiaĵon; eraro 403: Atingo malpermesita.\n\nKlopodu reŝargi paĝon per klavo F5, eble via seanco senvalidiĝis",
		"mm_e500": "Ne povas ludi aŭdiaĵon; eraro 500: Rigardu la protokolojn de servilo.",
		"mm_e5xx": "Ne povas ludi aŭdiaĵon; servila eraro ",
		"mm_nof": "neniuj aŭdio-dosieroj trovitaj proksime",
		"mm_prescan": "Serĉado por sekva aŭdiaĵo...",
		"mm_scank": "Sekva muzikaĵo trovita:",
		"mm_uncache": "kaŝmemoro malplenigita; ĉiuj muzikaĵoj estos reelŝutitaj dum sekva ludado",
		"mm_hnf": "ĉi tiu muzikaĵo ne ekzistas plu",

		"im_hnf": "ĉi tiu bildo ne ekzistas plu",

		"f_empty": 'ĉi tiu dosierujo estas malplena',
		"f_chide": 'ĉi tiu ago kaŝos kolumnon «{0}»\n\nvi povas malkaŝi kolumnojn en agordoj',
		"f_bigtxt": "ĉi tiu dosiero estas {0}-MiB-granda -- ĉu vere malfermi kiel teksto?",
		"f_bigtxt2": "ĉu malfermi nur la finon de dosiero? ĉi tiu reĝimo ankaŭ ŝaltos tujan ĝisdatigon, novaj linioj estos tuj montritaj",
		"fbd_more": '<div id="blazy"><code>{0}</code> de <code>{1}</code> dosieroj montrataj; <a href="#" id="bd_more">montri {2}</a> aŭ <a href="#" id="bd_all">montri ĉiujn</a></div>',
		"fbd_all": '<div id="blazy"><code>{0}</code> de <code>{1}</code> dosieroj montrataj; <a href="#" id="bd_all">montri ĉiujn</a></div>',
		"f_anota": "nur {0} de {1} eroj estis elektita;\nrulumi al la malsupro por elekti la tutan dosierujon",

		"f_dls": 'la ligiloj de dosieroj en ĉi tiu dosierujo estis\nanstataŭigitaj per elŝuto-ligiloj',

		"f_partial": "Por sendifekta elŝuto de nune-alŝutata dosiero, elektu dosieron kun sama nomo, sed sen etendaĵo <code>.PARTIAL</code>. Bonvolu uzi la butonon \"Rezigni\" aŭ klavon ESK por fari tion.\n\nSe vi uzas OK / Enter, la provizora dosiero <code>.PARTIAL</code> estos elŝutita, kiu tre probable enhavas nekompletajn datumojn.",

		"ft_paste": "alglui {0} erojn$NFulmoklavo: stir-V",
		"fr_eperm": 'ne povas alinomi:\nvi ne havas permeson “move” en ĉi tiu dosierujo',
		"fd_eperm": 'ne povas forigi:\nvi ne havas permeson “delete” en ĉi tiu dosierujo',
		"fc_eperm": 'ne povas eltondi:\nvi ne havas permeson “move” en ĉi tiu dosierujo',
		"fp_eperm": 'ne povas alglui:\nvi ne havas permeson “write” en ĉi tiu dosierujo',
		"fr_emore":  "elekti almenaŭ unu aĵon por alinomi",
		"fd_emore":  "elekti almenaŭ unu aĵon por forigi",
		"fc_emore":  "elekti almenaŭ unu aĵon por eltondi",
		"fcp_emore": "elekti almenaŭ unu aĵon por kopii al tondujo",

		"fs_sc": "kunhavigi la aktualan dosierujon",
		"fs_ss": "kunhavigi la elektitajn dosierojn",
		"fs_just1d": "vi ne povas elekti pli ol unu dosierujon\naŭ miksi dosierojn kaj dosierujojn en elektaĵo",
		"fs_abrt": "❌ ĉesigi",
		"fs_rand": "🎲 haz. nomo",
		"fs_go": "✅ krei komunaĵon",
		"fs_name": "nomo",
		"fs_src": "indiko",
		"fs_pwd": "pasvorto",
		"fs_exp": "tempolimo",
		"fs_tmin": "min",
		"fs_thrs": "horoj",
		"fs_tdays": "tagoj",
		"fs_never": "eterna",
		"fs_pname": "nomo de ligilo; estos hazarde kreita, se malplena",
		"fs_tsrc": "dosier(uj)o por kunhavigi",
		"fs_ppwd": "pasvorto (nedeviga)",
		"fs_w8": "kreado de komunaĵo...",
		"fs_ok": "premu <code>Enter/OK</code> por kopii al tondujo\npremu <code>ESK/Rezigni</code> por fermi",

		"frt_dec": "povas ripari difektitajn dosiernomojn\">url-malkodo",
		"frt_rst": "reagordi modifitajn dosiernomojn al originalaj\">↺ malfari",
		"frt_abrt": "ĉesigi operacion kaj fermi ĉi tiun fenestron\">❌ rezigni",
		"frb_apply": "ALINOMI",
		"fr_adv": "amasa / metadatuma / ŝablona alinomado\">altnivela",
		"fr_case": "uskleciva regula esprimo\">uskleco",
		"fr_win": "Windows-taŭgaj nomoj; signoj <code>&lt;&gt;:&quot;\\|?*</code> estos anstataŭigitaj per japanaj duobla-larĝaj signoj\">win",
		"fr_slash": "anstataŭigi <code>/</code>n per signo, kiu ne devigas kreadon de novaj dosierujoj\">sen /",
		"fr_re": "ŝablono de regula esprimo, kiu estos aplikita al originalaj dosiernomoj; kaptogrupoj povas esti referencita en formatkampo, ekz. &lt;code&gt;(1)&lt;/code&gt;, &lt;code&gt;(2)&lt;/code&gt; k.t.p.",
		"fr_fmt": "inspirita de foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; anstataŭigitas per nomo de muzikaĵo,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; preterpasas [ĉi tiun] parton, se artisto ne estas specifita$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; aldonas nulojn en trakonombro ĝis 2 ciferoj",
		"fr_pdel": "forigi",
		"fr_pnew": "konservi kiel",
		"fr_pname": "nomu vian novan ŝablonon",
		"fr_aborted": "ĉesigita",
		"fr_lold": "malnova nomo",
		"fr_lnew": "nova nomo",
		"fr_tags": "etikedoj por elektitaj dosieroj (ne redakteblas, nur por referenco):",
		"fr_busy": "alinomado de {0} aĵoj...\n\n{1}",
		"fr_efail": "alinomado malsukcesis:\n",
		"fr_nchg": "{0} da novaj nomoj estis modifita pro reguloj <code>win</code> kaj/aŭ <code>sen /</code>\n\nĈu daŭrigi kun modifitaj nomoj?",

		"fd_ok": "forigado sukcesis",
		"fd_err": "forigado malsukcesis:\n",
		"fd_none": "nenio estis forigita; eble servila eraro malpermesis ĝin (xbd)?",
		"fd_busy": "forigado de {0} aĵoj...\n\n{1}",
		"fd_warn1": "ĉu FORIGI ĉi tiujn {0} aĵojn?",
		"fd_warn2": "<b>Averto!</b> Ĉi tiu ago ne malfareblas. Ĉu forigi?",

		"fc_ok": "{0} aĵoj eltonditaj",
		"fc_warn": '{0} aĵoj eltonditaj\n\nnur <b>ĉi tiu</b> langeto de retumilo povas alglui ilin\n(pro la grando de elektaĵo)',

		"fcc_ok": "{0} aĵoj kopiitaj al tondujo",
		"fcc_warn": '{0} aĵoj kopiitaj al tondujo\n\nnur <b>ĉi tiu</b> langeto de retumilo povas alglui ilin\n(pro la grando de elektaĵo)',

		"fp_apply": "uzi ĉi tiujn nomojn",
		"fp_ecut": "unue eltondi aŭ kopii dosier(uj)ojn, do alglui ĝin poste\n\nnoto: tondujo ankaŭ funkcias inter aliaj langetoj de retumilo",
		"fp_ename": "{0} aĵoj ne povas esti movitaj, ĉar iliaj nomoj estas jam uzataj. Alinomi ilin sube aŭ lasi la nomokampojn malplenaj por preterpasi:",
		"fcp_ename": "{0} aĵoj ne povas esti kopiitaj, ĉar iliaj nomoj estas jam uzataj. Alinomi ilin sube aŭ lasi la nomokampojn malplenaj por preterpasi:",
		"fp_emore": "ankoraŭ restas koincidoj de dosiernomoj, kiuj bezonas solvon",
		"fp_ok": "movado sukcesis",
		"fcp_ok": "kopiado sukcesis",
		"fp_busy": "movado de {0} aĵoj...\n\n{1}",
		"fcp_busy": "kopiado {0} aĵoj...\n\n{1}",
		"fp_abrt": "ĉesigado...",
		"fp_err": "movado malsukcesis:\n",
		"fcp_err": "kopiado malsukcesis:\n",
		"fp_confirm": "ĉu movi tiujn {0} aĵojn ĉi tien?",
		"fcp_confirm": "ĉu kopii tiujn {0} aĵojn ĉi tien?",
		"fp_etab": 'eraro dum legado de tondujo el alia langeto de retumilo',
		"fp_name": "alŝutado de dosiero el via aparato. Nomi ĝin:",
		"fp_both_m":  '<h6>elektu, kion alglui</h6><code>Enter</code> = Movi {0} dosierojn al «{1}»\n<code>ESK</code> = Alŝuti {2} dosierojn el via aparato',
		"fcp_both_m": '<h6>elektu, kion alglui</h6><code>Enter</code> = Kopii {0} dosierojn al «{1}»\n<code>ESK</code> = Alŝuti {2} dosierojn el via aparato',
		"fp_both_b": '<a href="#" id="modal-ok">Movi</a><a href="#" id="modal-ng">Alŝuti</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopii</a><a href="#" id="modal-ng">Alŝuti</a>',

		"mk_noname": "tajpu nomon en tekstokampo maldekstre antaŭ vi faras ĉi tion :p",

		"tv_load": "Ŝargado de teksto-dokumento:\n\n{0}\n\n{1}% ({2} da {3} MiB ŝargita)",
		"tv_xe1": "ne povas ŝargi teksto-dosieron:\n\neraro ",
		"tv_xe2": "404, dosiero ne trovita",
		"tv_lst": "listo de teksto-dosieroj en",
		"tvt_close": "reveni al vido de dosierujo$NFulmoklavo: M (aŭ Esk)\">❌ fermi",
		"tvt_dl": "elŝuti ĉi tiun dosieron$NFulmoklavo: Y\">💾 elŝuti",
		"tvt_prev": "montri malsekvan dokumenton$NFulmoklavo: i\">⬆ malsekva",
		"tvt_next": "montri sekvan dokumenton$NFulmoklavo: K\">⬇ sekva",
		"tvt_sel": "elekti dosieron &nbsp; ( por eltondado / kopiado / forigado / ... )$NFulmoklavo: S\">elekti",
		"tvt_edit": "malfermi dosieron en teksto-redaktilo$NFulmoklavo: E\">✏️ redakti",
		"tvt_tail": "observi ŝanĝojn en dosiero; novaj linioj estos tuje montritaj\">📡 gvati",
		"tvt_wrap": "linifaldo\">↵",
		"tvt_atail": "alpingli rulumadon al malsupro de paĝo\">⚓",
		"tvt_ctail": "malkodi ANSI-kodojn de terminal-koloroj\">🌈",
		"tvt_ntail": "limo de rulumado (kiom da bajtoj de teksto konservi en memoro)",

		"m3u_add1": "muzikaĵo aldonita al m3u-ludlisto",
		"m3u_addn": "{0} muzikaĵoj aldonitaj al m3u-ludlisto",
		"m3u_clip": "m3u-ludlisto kopiita al tondujo\n\nvi devus krei tekst-dosieron kun etendaĵo <code>.m3u</code> kaj alglui la tekston en ĝi por krei uzeblan ludliston",

		"gt_vau": "ne montri videojn, nur ludi muzikaĵojn\">🎧",
		"gt_msel": "ŝalti elektado-reĝimon; stir-klaki dosieron por ne-elekta ago$N$N&lt;em&gt;kiam ŝaltita: duoblaklako por malfermi dosier(uj)on&lt;/em&gt;$N$NFulmoklavo: S\">elektado",
		"gt_crop": "stuci bildetojn\">stuci",
		"gt_3x": "alt-kvalitaj bildetoj\">3x",
		"gt_zoom": "grando",
		"gt_chop": "nomlongo",
		"gt_sort": "ordigi per",
		"gt_name": "nomo",
		"gt_sz": "grando",
		"gt_ts": "dato",
		"gt_ext": "tipo",
		"gt_c1": "pli mallongaj dosiernomoj",
		"gt_c2": "pli longaj dosiernomoj",

		"sm_w8": "serĉado...",
		"sm_prev": "serĉrezultoj sube venas al la lasta informpeto:\n  ",
		"sl_close": "fermi serĉrezultojn",
		"sl_hits": "montrado de {0} kongruaĵoj",
		"sl_moar": "ŝargi pli",

		"s_sz": "grando",
		"s_dt": "dato",
		"s_rd": "vojo",
		"s_fn": "nomo",
		"s_ta": "etikedoj",
		"s_ua": "alŝut📅",
		"s_ad": "aliaj",
		"s_s1": "minimuma MiB",
		"s_s2": "maksimuma MiB",
		"s_d1": "min. iso8601",
		"s_d2": "maks. iso8601",
		"s_u1": "alŝutita post",
		"s_u2": "kaj/aŭ antaŭ",
		"s_r1": "vojo enhavas &nbsp; (apartigi per spacoj)",
		"s_f1": "nomo enhavas &nbsp; (negacii per minuso)",
		"s_t1": "etikedoj enhavas &nbsp; (^=komenco, fino=$)",
		"s_a1": "ecoj de metadatumoj",

		"md_eshow": "ne povas montri ",
		"md_off": "[📜<em>readme</em>] malŝaltita en [⚙️] -- dokumento kaŝita",

		"badreply": "Eraro dum legado de respondo al servilo",

		"xhr403": "403: Atingo malpermesita\n\nklopodu reŝargi paĝon per klavo F5, eble via seanco senvalidiĝis",
		"xhr0": "nekonata (eble konekto al servilo estis perdita, aŭ servilo ne funkcias)",
		"cf_ok": "pardonon -- DD" + wah + "oS-protekto aktiviĝis\n\nĉio devus esti bona 30 sekundoj post\n\nse nenio okazas, reŝargi per klavo F5",
		"tl_xe1": "ne povas listigi subdosierujojn:\n\neraro ",
		"tl_xe2": "404: Dosierujo ne trovita",
		"fl_xe1": "ne povas listigi dosierojn en dosierujo:\n\neraro ",
		"fl_xe2": "404: Dosierujo ne trovita",
		"fd_xe1": "ne povas krei subdosierujon:\n\neraro ",
		"fd_xe2": "404: Patra dosierujo ne trovita",
		"fsm_xe1": "ne povas sendi mesaĝon:\n\neraro ",
		"fsm_xe2": "404: Patra dosierujo ne trovita",
		"fu_xe1": "ne povas ŝargi malsend-liston el servilo:\n\neraro ",
		"fu_xe2": "404: Dosiero ne trovita??",

		"fz_tar": "nedensigita dosiero GNU TAR (linux / mac)",
		"fz_pax": "nedensigita PAX-formata dosiero TAR (malpli rapide)",
		"fz_targz": "GNU TAR, densigita per 3a nivelo de GZip$N$Nkutime tre malrapida, do$Nuzu nedensigitan TARon anstataŭe",
		"fz_tarxz": "GNU TAR, densigita per 1a nivelo de XZ$N$Nkutime tre malrapida, do$Nuzu nedensigitan TARon anstataŭe",
		"fz_zip8": "Zip kun dosiernomoj laŭ UTF-8 (eble difektiĝis je Windows 7 kaj pli malnovaj)",
		"fz_zipd": "Zip kun dosiernomoj laŭ CP437, por tre malnovaj programoj (esperantaj diakritaĵoj ne funkcios)",
		"fz_zipc": "Zip, cp437, CRC-kontrolsumoj prekalkulitaj,$Npor MS-DOS PKZIP v2.04g (oktobro 1993)$N(bezonas pli da tempo antaŭ komenco de elŝuto)",

		"un_m1": "vi povas forigi viajn lastajn alŝutojn (aŭ ĉesigi nefinigitajn) sube",
		"un_upd": "reŝargi",
		"un_m4": "aŭ kunhavigi la dosierojn sube:",
		"un_ulist": "montri",
		"un_ucopy": "kopii",
		"un_flt": "nedeviga filtrilo:&nbsp; URL devas enhavi",
		"un_fclr": "vakigi filtrilon",
		"un_derr": 'malalŝutado malsukcesis:\n',
		"un_f5": 'io difektiĝis, bonvolu reŝargi aŭ uzi klavon F5',
		"un_uf5": "pardonu, sed vi devas reŝargi la paĝon (F5 aŭ Stir+R) antaŭ ĉesigi ĉi tiun alŝuton",
		"un_nou": '<b>averto:</b> servilo estas tro okupara por montri nefinigitajn alŝutojn; klaku la butonon "reŝargi" post kelkaj sekundoj',
		"un_noc": '<b>averto:</b> malalŝutado de tute alŝutitaj dosieroj estas malpermesita laŭ agordoj de servilo',
		"un_max": "unuaj 2000 dosieroj montritaj (uzi filtrilon por vidi aliajn)",
		"un_avail": "{0} lastaj alŝutoj forigeblas<br />{1} nefinigitajn ĉesigeblas",
		"un_m2": "ordigita per alŝuto-tempo, plej lastaj unue:",
		"un_no1": "neniuj sufiĉe lastaj alŝutoj",
		"un_no2": "neniuj sufiĉe lastaj alŝutoj, kongruaj laŭ filtrilo",
		"un_next": "forigi la sekvajn {0} dosierojn sube",
		"un_abrt": "ĉesigi",
		"un_del": "forigi",
		"un_m3": "ŝargado de viaj lastaj alŝutoj...",
		"un_busy": "forigado de {0} dosieroj...",
		"un_clip": "{0} ligiloj kopiitaj al tondujo",

		"u_https1": "vi devas",
		"u_https2": "ŝalti HTTPS-protokolon",
		"u_https3": "por pli bona rendimento",
		"u_ancient": 'via retumilo estas vere antikva -- eble vi devus <a href="#" onclick="goto(\'bup\')">uzi alŝutilon bup anstataŭe</a>',
		"u_nowork": "Firefox 53+ aŭ Chrome 57+ aŭ iOS 11+ necesas",
		"tail_2old": "Firefox 105+ aŭ Chrome 71+ aŭ iOS 14.5+ necesas",
		"u_nodrop": 'via retumilo estas tro malnova por ŝova-kaj-demeta alŝutado',
		"u_notdir": "tio ne estas dosierujo!\n\nvia retumilo estas tro malnova,\nbonvolu ŝovu kaj demetu anstataŭe",
		"u_uri": "por ŝovi-kaj-demeti bildon de aliaj fenestroj de retumiloj,\nbonvolu demeti ĝin sur la grandan alŝut-butonon",
		"u_enpot": 'uzi <a href="#">simplan fasadon</a> (povas plirapidigi alŝutojn)',
		"u_depot": 'uzi <a href="#">elegantan fasadon</a> (povas plimalrapidigi alŝutojn)',
		"u_gotpot": 'ŝaltado de simpla fasado por pli rapidaj alŝutoj,\n\nvi povas malŝalti ĝin, se ĝi ne plaĉas al vi!',
		"u_pott": "<p>dosieroj: &nbsp; <b>{0}</b> finitaj, &nbsp; <b>{1}</b> eraroj, &nbsp; <b>{2}</b> alŝutataj, &nbsp; <b>{3}</b> envicigitaj</p>",
		"u_ever": "ĉi tiu estas fundamenta alŝutilo; up2k postulas almenaŭ retumilojn<br>Chrome 21 // Firefox 13 // Edge 12 // Opera 12 // Safari 5.1",
		"u_su2k": 'ĉi tiu estas fundamenta alŝutilo; <a href="#" id="u2yea">up2k</a> estas pli bona',
		"u_uput": 'optimumigi por rapideco (ne kalkuli kontrolsumojn)',
		"u_ewrite": 'vi ne havas permeson skribi en ĉi tiun dosierujon',
		"u_eread": 'vi ne havas permeson legi ĉi tiun dosierujon',
		"u_enoi": 'serĉado de dosieroj estas malŝaltita en servilaj agordoj',
		"u_enoow": "anstataŭigo ne funkcios ĉi tie; forigo-permeso necesas",
		"u_badf": 'Ĉi tiuj {0} de {1} dosieroj estis preterpasitaj, eble pro permesoj de dosiersistemo:\n\n',
		"u_blankf": 'Ĉi tiuj {0} de {1} dosieroj estas blankaj; ĉu alŝuti malgraŭ tio?\n\n',
		"u_applef": 'Ĉi tiuj {0} de {1} dosieroj estas eble nedezirataj;\nPremu <code>OK/Enter</code> por PRETERPASI ilin,\nPremu <code>Rezigni/ESK</code> por ignori ĉi tiun mesaĝon kaj ALŜUTI ilin:\n\n',
		"u_just1": '\nEble ĝi funkcios pli bone, se vi elektas nur unu dosieron',
		"u_ff_many": "se vi uzas operaciumojn <b>Linux / MacOS / Android,</b> ĉi tiu kvanto de dosieroj <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>povas</em> kraŝi retumilon Firefox!</a>\nse ĉi tio okazos, klopodu denove (aŭ uzu Chrome-on).",
		"u_up_life": "Ĉi tiu alŝuto estos forigita de servilo\n{0} post kompletado",
		"u_asku": 'alŝuti ĉi tiujn {0} dosierojn al <code>{1}</code>',
		"u_unpt": "vi povas malalŝuti / forigi ĉi tiun alŝuton per 🧯 supre-maldesktre",
		"u_bigtab": '{0} dosieroj montrotaj\n\nĉi tiu povas kraŝi vian retumilon, ĉu daŭrigi?',
		"u_scan": 'Skanado de dosieroj...',
		"u_dirstuck": 'skanilo haltis dum atingado de sekvaj {0} dosieroj; ili estos preterpasitaj:',
		"u_etadone": 'Finita ({0}, {1} dosieroj)',
		"u_etaprep": '(preparado por alŝutado)',
		"u_hashdone": 'kontrolsumita',
		"u_hashing": 'k-sumado',
		"u_hs": 'kvitanco...',
		"u_started": "la dosieroj estas alŝutataj; rigardu [🚀]",
		"u_dupdefer": "duplikatoj; estos traktita post ĉiuj aliaj dosieroj",
		"u_actx": "alklaku ĉi tiun tekston por eviti malrapidigon<br />dum uzado de aliaj fenestroj/langetoj",
		"u_fixed": "Bone!&nbsp; Riparita 👍",
		"u_cuerr": "alŝutado de ero {0} de {1} malsukcesis;\neble malgravas, alŝutado daŭrigas\n\ndosiero: {2}",
		"u_cuerr2": "servilo rifuzis alŝutadon (ero {0} de {1});\nprovos denove poste\n\ndosiero: {2}\n\neraro ",
		"u_ehstmp": "reprovos poste; rigardu sube-dekstre",
		"u_ehsfin": "servilo rifuzis peton por finigi alŝutadon; reprovado...",
		"u_ehssrch": "servilo rifuzis peton por ŝerco; reprovado...",
		"u_ehsinit": "servilo rifuzis peton por komenco de alŝutado; reprovado...",
		"u_eneths": "reta eraro dum alŝutada kvitanco; reprovado...",
		"u_enethd": "reta eraro dum kontrolo de ekzistado de cela dosiero; reprovado...",
		"u_cbusy": "atendado, por ke la servilo estas atingebla post reta eraro...",
		"u_ehsdf": "servilo ne havas sufiĉe da diskospaco!\n\nla alŝutado reprovos daŭre, okaze de iu liberigas\nsufiĉe da diskospaco",
		"u_emtleak1": "ŝajnas, ke via retumilo likas memoron; \nbonvolu",
		"u_emtleak2": ' <a href="{0}">uzi protokolon HTTPS (rekomendita)</a> aŭ ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'provu fari tiel:\n<ul><li>reŝargu la paĝon per klavo <code>F5</code></li><li>, do malŝalti la butonon &nbsp;<code>mt</code>&nbsp; en la &nbsp;<code>⚙️ agordoj</code></li><li>kaj reprovu alŝuton</li></ul>Alŝuto estos pli malrapida, sed nenio fareblas.\nPardonon por la ĝenaĵo!\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">korektis ĉi tion</a>',
		"u_emtleakf": 'provu fari tiel:\n<ul><li>reŝargu la paĝon per klavo <code>F5</code></li><li>, do malŝalti la butonon &nbsp;<code>mt</code>&nbsp; en la &nbsp;<code>⚙️ agordoj</code></li><li>kaj reprovu alŝuton</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">espereble korektos ĉi tion</a> baldaŭ',
		"u_s404": "ne trovita ĉe la servilo",
		"u_expl": "klarigi",
		"u_maxconn": "plimulto da retumiloj ne permesas uzi pli ol 6, sed Firefox havas agordon <code>connections-per-server</code> en <code>about:config</code>, per kiu la limo ŝanĝeblas",
		"u_tu": '<p class="warn">AVERTO: rapidega reĝimo ŝaltita, <span>&nbsp;kliento povas ne detekti kaj daŭrigi nefinigitajn alŝutojn; rigardu la ŝpruchelpilon de rapidega-butono</span></p>',
		"u_ts": '<p class="warn">AVERTO: rapidega reĝimo ŝaltita, <span>&nbsp;serĉrezultoj povas esti eraraj; rigardu la ŝpruchelpilon de rapidega-butono</span></p>',
		"u_turbo_c": "rapidega reĝimo estas malpermesita laŭ servilaj agordoj",
		"u_turbo_g": "rapidega reĝimo estas malpermesita, ĉar vi\nne rajtas listigi dosierujojn en ĉi tiu datumportilo",
		"u_life_cfg": 'aŭtoforigado post <input id="lifem" p="60" /> minutoj (aŭ <input id="lifeh" p="3600" /> horoj)',
		"u_life_est": 'alŝuto estos forigita je <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'ĉi tiu dosierujo postulas \naŭtoforigadon de dosieroj post {0}',
		"u_unp_ok": 'malalŝuto permesitas por {0}',
		"u_unp_ng": 'malalŝuto NE estos permesita',
		"ue_ro": 'via atingo de ĉi tiu dosierujo estas nur-lega\n\n',
		"ue_nl": 'vi ne estas ensalutita',
		"ue_la": 'vi estas ensalutita kiel "{0}"',
		"ue_sr": 'vi estas en serĉo-reĝimo nun\n\nŝanĝi al alŝuto-reĝimo per lupeo-simbolo 🔎 (apude de la grandega SERĈO-butono), kaj provu alŝuti denove\n\npardonon',
		"ue_ta": 'provu alŝuti denove, ĝi devus funkcii nun',
		"ue_ab": "ĉi tiu dosiero estas jam alŝutata en alian dosierujon, tiu alŝutado devas esti finigita antaŭ alŝutado de la sama dosiero en alian lokon.\n\nVi povas ĉesigi la nunan alŝutadon per butonon 🧯 supre-maldekstre",
		"ur_1uo": "OK: Dosiero sukcese alŝutita",
		"ur_auo": "OK: Ĉiuj {0} dosieroj sukcese alŝutitaj",
		"ur_1so": "OK: Dosiero trovita ĉe la servilo",
		"ur_aso": "OK: Ĉiuj {0} dosieroj trovitaj ĉe la serviloj",
		"ur_1un": "Alŝutado malsukcesis, pardonon",
		"ur_aun": "Ĉiuj {0} alŝutadoj malsukcesis, pardonon",
		"ur_1sn": "Dosiero estis NE trovita ĉe la servilo",
		"ur_asn": "La {0} dosieroj estis NE trovitaj ĉe la servilo",
		"ur_um": "Finita;\n{0} alŝutoj sukcesis,\n{1} alŝutoj malsukcesis, pardonon",
		"ur_sm": "Finita;\n{0} dosieroj trovitaj ĉe la servilo,\n{1} dosieroj NE trovitaj ĉe la servilo",

		"lang_set": "ĉu reŝargi paĝon por efektivigi lingvo-ŝanĝon?",
	},
	"fin": {
		"tt": "Suomi",

		"cols": {
			"c": "toimintopainikkeet",
			"dur": "kesto",
			"q": "laatu / bittinopeus",
			"Ac": "äänikoodekki",
			"Vc": "videokoodekki",
			"Fmt": "formaatti / säiliö",
			"Ahash": "äänen tarkistussumma",
			"Vhash": "videon tarkistussumma",
			"Res": "resoluutio",
			"T": "tiedostotyyppi",
			"aq": "äänenlaatu / bittinopeus",
			"vq": "kuvalaatu / bittinopeus",
			"pixfmt": "alinäytteistys / pikselirakenne",
			"resw": "horisontaalinen resoluutio",
			"resh": "vertikaalinen resoluutio",
			"chs": "äänikanavat",
			"hz": "näytteenottotaajuus"
		},

		"hks": [
			[
				"misc",
				["ESC", "sulje asioita"],

				"file-manager",
				["G", "vaihda lista/kuvanäkymään"],
				["T", "vaihda pienoiskuviin/kuvakkeisiin"],
				["⇧ A/D", "pienoiskuvien koko"],
				["ctrl-K", "poista valitut"],
				["ctrl-X", "siirrä valitut leikepöydälle"],
				["ctrl-C", "kopioi valitut leikepöydälle"],
				["ctrl-V", "siirrä tai kopioi tähän"],
				["Y", "lataa valitut"],
				["F2", "uudelleennimeä valitut"],

				"file-list-sel",
				["space", "vaihda tiedostonvalintatilaan"],
				["↑/↓", "siirrä valintaosoitinta"],
				["ctrl ↑/↓", "siirrä osoitinta ja näkymää"],
				["⇧ ↑/↓", "valitse edellinen/seuraava tiedosto"],
				["ctrl-A", "valitse kaikki tiedostot / hakemistot"],
			], [
				"navigation",
				["B", "näytä linkkipolku"],
				["I/K", "siirry edelliseen/seuraavaan hakemistoon"],
				["M", "siirry ylähakemistoon/supista nykyinen hakemisto"],
				["V", "näytä hakemistot/tekstitiedostot navigointipaneelissa"],
				["A/D", "navigointipaneelin koko"],
			], [
				"audio-player",
				["J/L", "edellinen/seuraava kappale"],
				["U/O", "kelaa 10s taaksepäin/eteenpäin"],
				["0..9", "siirry 0%..90%"],
				["P", "toista/pysäytä kappale"],
				["S", "valitse toistossa oleva kappale"],
				["Y", "lataa kappale"],
			], [
				"image-viewer",
				["J/L, ←/→", "edellinen/seuraava kuva"],
				["Home/End", "ensimmäinen/viimeinen kuva"],
				["F", "siirry koko näytön tilaan"],
				["R", "kierrä myötäpäivään"],
				["⇧ R", "kierrä vastapäivään"],
				["S", "valitse kuva"],
				["Y", "lataa kuva"],
			], [
				"video-player",
				["U/O", "kelaa 10s taaksepäin/eteenpäin"],
				["P/K/Space", "toista/pysäytä video"],
				["C", "jatka toistoa seuraavaan videoon"],
				["V", "toista uudelleen"],
				["M", "vaimenna"],
				["[ ja ]", "aseta videon uudelleentoistoväli"],
			], [
				"textfile-viewer",
				["I/K", "edellinen/seuraava tiedosto"],
				["M", "sulje tekstitiedosto"],
				["E", "muokkaa tekstitiedostoa"],
				["S", "valitse tiedosto (leikkausta/kopiointia/uudelleennimeämistä varten)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Peruuta",

		"enable": "Aktivoi",
		"danger": "HUOMIO!",
		"clipped": "kopioitu leikepöydälle",

		"ht_s1": "sekunti",
		"ht_s2": "sekuntia",
		"ht_m1": "minuutti",
		"ht_m2": "minuuttia",
		"ht_h1": "tunti",
		"ht_h2": "tuntia",
		"ht_d1": "päivä",
		"ht_d2": "päivää",
		"ht_and": " ja ",

		"goh": "hallintapaneeli",
		"gop": 'viereinen hakemisto">edell',
		"gou": 'ylempi hakemisto">ylös',
		"gon": 'seuraava hakemisto">seur',
		"logout": "Kirjaudu ulos ",
		"login": "Kirjaudu sisään", //m
		"access": " -oikeudet",
		"ot_close": "sulje alavalikko",
		"ot_search": "etsi tiedostoja ominaisuuksien, tiedostopolun tai -nimen, musiikkitägien tai näiden yhdistelmän perusteella$N$N&lt;code&gt;foo bar&lt;/code&gt; = täytyy sisältää sekä «foo» että «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = täytyy sisältää «foo» mutta ei «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = alkaa «yana» ja on «opus»-tiedosto$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = sisältää täsmälleen «try unite»$N$Npäivämäärän muoto on iso-8601, kuten$N&lt;code&gt;2009-12-31&lt;/code&gt; tai &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: poista viimeaikaiset tai keskeytä keskeneräiset lataukset",
		"ot_bup": "bup: tiedostojen 'perus'lähetysohjelma, tukee jopa netscape 4.0",
		"ot_mkdir": "mkdir: luo uusi hakemisto",
		"ot_md": "new-md: luo uusi markdown-dokumentti",
		"ot_msg": "msg: lähetä viesti palvelinlokiin",
		"ot_mp": "mediasoittimen asetukset",
		"ot_cfg": "asetukset",
		"ot_u2i": 'up2k: lähetä tiedostoja (vaatii write-oikeudet) tai vaihda hakutilaan nähdäksesi, ovatko tiedostot jo olemassa jossain päin palvelinta$N$Nlatauksia voi jatkaa, ne ovat monisäikeistettyjä, ja tiedostojen aikaleimat säilytetään; nuijii prosessoria enemmän kuin [🎈]&nbsp; (peruslatausohjelma)<br /><br />tiedostojen lähetyksen aikana tämä kuvake muuttuu kertoo lähetyksen edistymisestilanteen!',
		"ot_u2w": 'up2k: lähetä tiedostoja jatkamistoiminnolla (voit sulkea selaimen ja vetää samat tiedostot selainikkunaan myöhemmin)$N$monisäikeistetty, ja tiedostojen aikaleimat säilyvät; nuijii prosessoria enemmän kuin [🎈]&nbsp; (peruslatausohjelma)<br /><br />tiedostojen lähetyksen aikana tämä kuvake muuttuu kertoo lähetyksen edistymisestilanteen!',
		"ot_noie": 'Suosittelemme käyttämään uudempaa selainta.',

		"ab_mkdir": "luo hakemisto",
		"ab_mkdoc": "luo markdown-tiedosto",
		"ab_msg": "lähetä viesti palvelinlokiin",

		"ay_path": "siirry hakemistoihin",
		"ay_files": "siirry tiedostoihin",

		"wt_ren": "uudelleennimeä valitut kohteet$NPikanäppäin: F2",
		"wt_del": "poista valitut kohteet$NPikanäppäin: ctrl-K",
		"wt_cut": "siirrä valitut kohteet leikepöydälle &lt;small&gt;(siirtääksesi ne muualle)&lt;/small&gt;$NPikanäppäin: ctrl-X",
		"wt_cpy": "kopioi valitut kohteet leikepöydälle$N(liittääksesi ne muualle)$NPikanäppäin: ctrl-C",
		"wt_pst": "liitä aiemmin leikatut / kopioidut valinnat$NPikanäppäin: ctrl-V",
		"wt_selall": "valitse kaikki tiedostot$NPikanäppäin: ctrl-A (kun tiedosto on kohdistettu)",
		"wt_selinv": "valitse vastakkaiset tiedostot",
		"wt_zip1": "lataa tämä hakemisto pakattuna",
		"wt_selzip": "lataa valitut kohteet pakattuna",
		"wt_seldl": "lataa valitut kohteet paketoimatta$NPikanäppäin: Y",
		"wt_npirc": "kopioi kappaletiedot IRC-muotoilulla",
		"wt_nptxt": "kopioi kappaletiedot ilman muotoilua",
		"wt_m3ua": "lisää m3u-soittolistaan (klikkaa <code>📻kopioi</code> myöhemmin)",
		"wt_m3uc": "kopioi m3u-soittolista leikepöydälle",
		"wt_grid": "vaihda kuva- ja listanäkymän välillä$NPikanäppäin: G",
		"wt_prev": "edellinen kappale$NPikanäppäin: J",
		"wt_play": "toista / pysäytä$NPikanäppäin: P",
		"wt_next": "seuraava kappale$NPikanäppäin: L",

		"ul_par": "rinnakkaislatausten lkm:",
		"ut_rand": "satunnaisgeneroidut tiedostonimet",
		"ut_u2ts": "kopioi viimeksi muokattu aikaleima$Ntiedostojärjestelmästäsi palvelimelle\">📅",
		"ut_ow": "korvaa olemassa olevat tiedostot palvelimella?$N🛡️: ei koskaan (luo sen sijaan uuden tiedostonimen)$N🕒: korvaa jos palvelintiedosto on vanhempi kuin omasi$N♻️: korvaa aina jos tiedostot ovat erilaisia",
		"ut_mt": "jatka muiden tiedostojen tiivisteiden laskemista latauksen aikana$N$Nkannattanee poistaa käytöstä, mikäli prosessori tai kovalevy on vanhempaa mallia",
		"ut_ask": 'kysy vahvistusta ennen latauksen aloittamista">💭',
		"ut_pot": "paranna latausnopeutta hitailla laitteilla$Nvähentämällä käyttöliittymän monimutkaisuutta",
		"ut_srch": "lataamisen sijaan tarkista, ovatko tiedostot jo $N olemassa palvelimella (käy läpi kaikki hakemistot, joihin sinulla on read-oikeudet)",
		"ut_par": "keskeytä lataukset asettamalla se nollaan$N$Nnosta, jos yhteytesi on hidas tai viive on suuri$N$Npidä se 1:ssä lähiverkossa tai jos palvelimen kovalevy on pullonkaula",
		"ul_btn": "vedä tiedostoja / hakemistoja tähän<br>(tai klikkaa minua)",
		"ul_btnu": "L Ä H E T Ä",
		"ul_btns": "E T S I",

		"ul_hash": "tiiviste",
		"ul_send": "lähetä",
		"ul_done": "valmis",
		"ul_idle1": "ei latauksia jonossa",
		"ut_etah": "keskimääräinen &lt;em&gt;tiivisteiden lasku&lt;/em&gt;nopeus ja arvioitu aika valmistumiseen",
		"ut_etau": "keskimääräinen &lt;em&gt;lataus&lt;/em&gt;nopeus ja arvioitu aika valmistumiseen",
		"ut_etat": "keskimääräinen &lt;em&gt;kokonais&lt;/em&gt;nopeus ja arvioitu aika valmistumiseen",

		"uct_ok": "onnistui",
		"uct_ng": "ei-hyvä: epäonnistui / hylätty / ei löydy",
		"uct_done": "ok ja ng yhdistettynä",
		"uct_bz": "laskee tiivisteitä tai lataa",
		"uct_q": "tyhjäkäynnillä, odottaa",

		"utl_name": "tiedostonimi",
		"utl_ulist": "lista",
		"utl_ucopy": "kopioi",
		"utl_links": "linkit",
		"utl_stat": "tila",
		"utl_prog": "edistyminen",

		// keep short:
		"utl_404": "404",
		"utl_err": "VIRHE",
		"utl_oserr": "Käyttöjärjestelmävirhe",
		"utl_found": "löytyi",
		"utl_defer": "lykkää",
		"utl_yolo": "YOLO",
		"utl_done": "valmis",

		"ul_flagblk": "tiedostot lisättiin jonoon</b><br>mutta toisen selainvälilehden up2k on kiireinen,<br>joten odotetaan sen valmistumista ensin",
		"ul_btnlk": "palvelinkonfiguraatio on lukinnut tämän kytkimen tähän tilaan",

		"udt_up": "Lataa",
		"udt_srch": "Etsi",
		"udt_drop": "pudota se tähän",

		"u_nav_m": '<h6>selvä, mitäs sulla on?</h6><code>Enter</code> = Tiedostoja (yksi tai useampi)\n<code>ESC</code> = Yksi hakemisto (mukaan lukien alihakemistot)',
		"u_nav_b": '<a href="#" id="modal-ok">Tiedostoja</a><a href="#" id="modal-ng">Yksi hakemisto</a>',

		"cl_opts": "asetukset",
		"cl_themes": "teema",
		"cl_langs": "kieli",
		"cl_ziptype": "hakemiston pakkaustyyppi",
		"cl_uopts": "up2k-kytkimet",
		"cl_favico": "favicon",
		"cl_bigdir": "suuret hakemistot",
		"cl_hsort": "#sort",
		"cl_keytype": "sävellajin notaatiotyyppi",
		"cl_hiddenc": "piilotetut sarakkeet",
		"cl_hidec": "piilota",
		"cl_reset": "palauta",
		"cl_hpick": "napauta sarakeotsikoita piilottaaksesi alla olevassa taulukossa",
		"cl_hcancel": "sarakkeiden piilotus peruttu",

		"ct_grid": '田 kuvanäkymä',
		"ct_ttips": '◔ ◡ ◔">ℹ️ vihjelaatikot',
		"ct_thumb": 'valitse kuvakkeiden / pienoiskuvien välillä kuvanäkymässä $NPikanäppäin: T">🖼️ pienoiskuvat',
		"ct_csel": 'käytä CTRL ja SHIFT tiedostojen valintaan kuvanäkymässä">valitse',
		"ct_ihop": 'kun kuvakatselin suljetaan, vieritä alas viimeksi katsottuun tiedostoon">g⮯',
		"ct_dots": 'näytä piilotetut tiedostot (jos palvelin sallii)">piilotiedostot',
		"ct_qdel": 'kysy vahvistusta vain kerran tiedostoja poistaessa">qdel',
		"ct_dir1st": 'lajittele hakemistot ennen tiedostoja">📁 ensin',
		"ct_nsort": 'luonnollinen lajittelu (tiedostonimille jotka ovat numeroalkuisia)">nsort',
		"ct_utc": 'näytä kaikki aikaleimat UTC-ajassa">UTC',
		"ct_readme": 'näytä README.md hakemistolistauksissa">📜 readme',
		"ct_idxh": 'näytä index.html hakemistolistan sijasta">htm',
		"ct_sbars": 'näytä vierityspalkit">⟊',

		"cut_umod": "jos tiedosto on jo olemassa palvelimella, päivitä palvelimen viimeksi muokattu aikaleima vastaamaan paikallista tiedostoasi (vaatii write- ja delete-oikeudet)\">re📅",

		"cut_turbo": "yolo-painike -- et todennäköisesti halua ottaa tätä käyttöön:$N$Nkäytä tätä jos latasit valtavan määrän tiedostoja ja jouduit käynnistämään uudelleen jostain syystä, ja haluat jatkaa latausta välittömästi$N$Ntämä korvaa tiivistetarkistuksen yksinkertaisella <em>&quot;onko tällä sama tiedostokoko palvelimella?&quot;</em> joten jos tiedoston sisältö on erilainen sitä EI ladata$N$Nsinun pitäisi poistaa tämä käytöstä kun lataus on valmis, ja sitten &quot;ladata&quot; samat tiedostot uudelleen antaaksesi selaimesi varmistaa ne\">turbo",

		"cut_datechk": "ei vaikutusta ellei turbo-painike ole käytössä$N$Nvähentää yolo-tekijää hieman; tarkistaa vastaavatko tiedostojen aikaleimat palvelimella omia$N$Npitäisi <em>teoriassa</em> napata useimmat keskeneräiset / vioittuneet lataukset, mutta ei ole korvike varmistuskierrokselle turbo poistettuna käytöstä jälkeenpäin\">päiväysvarmistin",

		"cut_u2sz": "kunkin lähetyspalan koko (MiB:ssä); suuret arvot lentävät paremmin atlantin yli. kokeile pieniä arvoja erittäin heikoilla yhteyksillä",

		"cut_flag": "varmista että vain yksi välilehti lataa kerrallaan $N -- muissa välilehdissä täytyy olla tämä käytössä myös $N -- vaikuttaa vain saman verkkotunnuksen välilehtiin",

		"cut_az": "lähetä tiedostot aakkosjärjestyksessä, eikä pienin-tiedosto-ensiksi$N$Naakkosjärjestys voi tehdä helpommaksi silmäillä jos jokin meni vikaan palvelimella, mutta se tekee latauksesta hieman hitaamman kuitu- ja lähiverkossa",

		"cut_nag": "käyttöjärjestelmäilmoitus kun lataus valmistuu$N(vain jos selain tai välilehti ei ole aktiivinen)",
		"cut_sfx": "äänivaroitus kun lataus valmistuu$N(vain jos selain tai välilehti ei ole aktiivinen)",

		"cut_mt": "monisäikeistä tiedostojen tiivistysarvojen laskeminen$N$Ntämä käyttää web-workereitä ja vaatii$Nenemmän RAM-muistia (jopa 512 MiB ekstraa)$N$Ntekee https:n 30% nopeammaksi, http:n 4.5x nopeammaksi\">mt",

		"cut_wasm": "käytä wasm:ia selaimen sisäänrakennetun tiivistäjän sijaan; parantaa nopeutta chrome-pohjaisissa selaimissa mutta lisää prosessorikuormaa, ja monissa vanhemmissa chrome-versioissa on bugeja jotka saavat selaimen kuluttamaan kaiken RAM-muistin ja kaatumaan jos tämä on käytössä\">wasm",

		"cft_text": "favicon-teksti (tyhjennä ja päivitä poistaaksesi käytöstä)",
		"cft_fg": "edustaväri",
		"cft_bg": "taustaväri",

		"cdt_lim": "tiedostojen enimmäismäärä näytettäväksi hakemistossa",
		"cdt_ask": "sivun lopussa, sen sijaan että lataa $Nautomaattisesti lisää tiedostoja, kysy mitä tehdä",
		"cdt_hsort": "kuinka monta lajittelusääntöä (&lt;code&gt;,sorthref&lt;/code&gt;) sisällyttää media-URL:eihin. Tämän asettaminen nollaan jättää myös huomioimatta media-linkeissä sisällytetyt lajittelusäännöt kun napsautat niitä",

		"tt_entree": "näytä navigointipaneeli$NPikanäppäin: B",
		"tt_detree": "näytä linkkipolku$NPikanäppäin: B",
		"tt_visdir": "näytä valittu hakemisto",
		"tt_ftree": "vaihda linkkipolku- / tekstitiedostonäkymään$NPikanäppäin: V",
		"tt_pdock": "näytä ylähakemistot telakoitussa paneelissa ylhäällä",
		"tt_dynt": "kasvata automaattisesti hakemistosyvyyden kasvaessa",
		"tt_wrap": "rivitys",
		"tt_hover": "paljasta ylivuotavat rivit leijutettaessa$N( rikkoo vierityksen ellei hiiri $N&nbsp; ole vasemmassa marginaalissa )",

		"ml_pmode": "hakemiston lopussa...",
		"ml_btns": "komennot",
		"ml_tcode": "muunna nämä",
		"ml_tcode2": "tähän muotoon",
		"ml_tint": "sävy",
		"ml_eq": "taajuuskorjain",
		"ml_drc": "dynaaminen alueen kompressori",

		"mt_loop": "toista samaa kappaletta\">🔁",
		"mt_one": "lopeta yhden toiston jälkeen\">1️⃣",
		"mt_shuf": "aktivoi satunnaistoisto\">🔀",
		"mt_aplay": "automaattitoisto jos linkissä jolla pääsit palvelimelle oli kappale-ID$N$Ntämän poistaminen käytöstä pysäyttää myös sivun URL:n päivittämisen kappale-ID:lla musiikkia toistettaessa, estääksesi automaattitoiston jos nämä asetukset menetetään mutta URL säilyy\">a▶",
		"mt_preload": "aloita seuraavan kappaleen lataaminen lähellä loppua, mahdollistaen saumattoman toiston\">esilataus",
		"mt_prescan": "siirry seuraavaan hakemistoon ennen viimeisen kappaleen$Nloppumista, pitäen verkkoselaimen tyytyväisenä$Njotta se ei pysäytä toistoa\">nav",
		"mt_fullpre": "yritä esiladata koko kappale;$N✅ ota käyttöön <b>heikoilla</b> yhteyksillä,$N❌ <b>poista käytöstä</b> hitailla yhteyksillä\">esi+",
		"mt_fau": "puhelimissa: estä musiikin pysähtyminen jos seuraava kappale ei esilataudu tarpeeksi nopeasti (voi aiheuttaa ongelmia kappaletietojen näyttämisessä)\">☕️",
		"mt_waves": "aaltomuoto-hakupalkki:$Nnäytä äänenvahvuus selaimessa\">~s",
		"mt_npclip": "näytä painikkeet parhaillaan soivan kappaleen leikepöydälle kopioimiseen\">/np",
		"mt_m3u_c": "näytä painikkeet valittujen$Nkappaleiden kopioimiseen m3u8-soittolistana leikepöydälle\">📻",
		"mt_octl": "käyttöjärjestelmäintegraatio (medianäppäimet / osd)\">os-ctl",
		"mt_oseek": "salli haku käyttöjärjestelmäintegraation kautta$N$Nhuom: joissakin laitteissa (iPhonet),$Ntämä korvaa 'seuraava kappale' -painikkeen\">kelaus",
		"mt_oscv": "näytä albumin kansi osd:ssä\">kansikuvat",
		"mt_follow": "pidä soiva kappale näkyvissä\">🎯",
		"mt_compact": "kompaktit säätimet\">⟎",
		"mt_uncache": "tyhjennä välimuisti &nbsp;(kokeile tätä jos selaimesi välimuistissa on$Nrikkinäinen kopio kappaleesta)\">uncache",
		"mt_mloop": "toista avoinna olevaa hakemistoa loputtomasti\">🔁 alkuun",
		"mt_mnext": "lataa seuraava hakemisto ja jatka\">📂 seuraava",
		"mt_mstop": "pysäytä toisto\">⏸ pysäytä",
		"mt_cflac": "muunna flac / wav {0}-muotoon\">flac",
		"mt_caac": "muunna aac / m4a {0}-muotoon\">aac",
		"mt_coth": "muunna kaikki muut paitsi mp3 {0}-muotoon\">muut",
		"mt_c2opus": "paras valinta pöytäkoneille, kannettaville, androidille\">opus",
		"mt_c2owa": "opus-weba, iOS 17.5:lle ja uudemmille\">owa",
		"mt_c2caf": "opus-caf, iOS 11:lle - 17:lle\">caf",
		"mt_c2mp3": "käytä tätä erittäin vanhoissa laitteissa\">mp3",
		"mt_c2flac": "paras äänenlaatu, mutta isot lataukset\">flac", //m
		"mt_c2wav": "pakkaamaton toisto (vielä suurempi tiedosto)\">wav", //m
		"mt_c2ok": "hienoa, hyvä valinta",
		"mt_c2nd": "tuo ei ole suositeltu formaatti laitteellesi, mutta tee miten lystäät",
		"mt_c2ng": "laitteesi ei näytä tukevan tätä formaattia, mutta yritetään nyt silti",
		"mt_xowa": "iOS:ssä on bugeja jotka estävät taustatoiston tällä formaatilla; käytä caf:ia tai mp3:a sen sijaan",
		"mt_tint": "taustan taso (0-100) liukupalkissa$Ntehden puskuroinnista vähemmän häiritsevän",
		"mt_eq": "aktivoi taajuuskorjaimen ja vahvistussäätimen;$N$Nvahvistus &lt;code&gt;0&lt;/code&gt; = normaali 100% äänenvoimakkuus (muokkaamaton)$N$Nleveys &lt;code&gt;1 &nbsp;&lt;/code&gt; = normaali stereo (muokkaamaton)$Nleveys &lt;code&gt;0.5&lt;/code&gt; = 50% vasen-oikea ristisyöttö$Nleveys &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nvahvistus &lt;code&gt;-0.8&lt;/code&gt; &amp; leveys &lt;code&gt;10&lt;/code&gt; = laulun poisto :^)$N$Nequalizerin käyttöönotto tekee saumattomista albumeista täysin saumattomia, joten jätä se päälle kaikilla arvoilla nollassa (paitsi leveys = 1) jos välität siitä",
		"mt_drc": "aktivoi dynaamisen alueen kompressorin; ottaa myös käyttöön taajuuskorjaimen tasapainottamaan spagettia, joten aseta kaikki EQ-kentät paitsi 'leveys' nollaan jos et halua sitä$N$Nalentaa äänenvoimakkuutta KYNNYS dB:n yläpuolella; jokaisesta SUHDE dB:stä KYNNYKSEN yli tulee 1 dB ulos, joten oletusarvot kynnys -24 ja suhde 12 tarkoittaa ettei sen pitäisi koskaan tulla kovempaa kuin -22 dB ja on turvallista nostaa equalizerin vahvistus 0.8:aan, tai jopa 1.8:aan ATK 0:lla ja valtavalla RLS:llä kuten 90 (toimii vain firefoxissa; RLS on max 1 muissa selaimissa)$N$N(katso wikipedia, he selittävät sen paljon paremmin)",

		"mb_play": "toista",
		"mm_hashplay": "soita tämä äänitiedosto?",
		"mm_m3u": "paina <code>Enter/OK</code> Toistaaksesi\npaina <code>ESC/Peruuta</code> Muokataksesi",
		"mp_breq": "tarvitset firefox 82+ tai chrome 73+ tai iOS 15+",
		"mm_bload": "ladataan...",
		"mm_bconv": "muunnetaan muotoon {0}, odota...",
		"mm_opusen": "selaimesi ei voi toistaa aac / m4a -tiedostoja;\ntranskoodaus opukseen on nyt käytössä",
		"mm_playerr": "toisto epäonnistui: ",
		"mm_eabrt": "Toistoyritys peruttiin",
		"mm_enet": "Internet-yhteytesi on epävakaa",
		"mm_edec": "Tämä tiedosto on väitetysti vioittunut??",
		"mm_esupp": "Selaimesi ei ymmärrä tätä äänimuotoa",
		"mm_eunk": "Tuntematon virhe",
		"mm_e404": "Kappaletta ei voitu toistaa; virhe 404: Tiedostoa ei löydy.",
		"mm_e403": "Kappaletta ei voitu toistaa; virhe 403: Pääsy kielletty.\n\nKokeile painaa F5 päivittääksesi, ehkä kirjauduit ulos",
		"mm_e500": "Kappaletta ei voitu toistaa; virhe 500: Tarkista palvelinlokit.",
		"mm_e5xx": "Kappaletta ei voitu toistaa; palvelinvirhe ",
		"mm_nof": "ei löydy enempää äänitiedostoja lähistöltä",
		"mm_prescan": "Etsitään musiikkia toistettavaksi seuraavaksi...",
		"mm_scank": "Löytyi seuraava kappale:",
		"mm_uncache": "välimuisti tyhjennetty; kaikki kappaleet ladataan uudelleen seuraavalla toistolla",
		"mm_hnf": "tuota kappaletta ei enää ole olemassa",

		"im_hnf": "tuota kuvaa ei enää ole olemassa",

		"f_empty": 'tämä hakemisto on tyhjä',
		"f_chide": 'tämä piilottaa sarakkeen «{0}»\n\nvoit palauttaa sarakkeet asetuksista',
		"f_bigtxt": "tämä tiedosto on {0} Mt kokoinen -- näytetäänkö silti tekstinä?",
		"f_bigtxt2": "näytetäänkö vain tiedoston loppu? tämä myös mahdollistaa seuraamisen/tailing, näyttäen uudet tekstirivit reaaliaikaisesti",
		"fbd_more": '<div id="blazy">näytetään <code>{0}</code> / <code>{1}</code> tiedostoa; <a href="#" id="bd_more">näytä {2}</a> tai <a href="#" id="bd_all">näytä kaikki</a></div>',
		"fbd_all": '<div id="blazy">näytetään <code>{0}</code> / <code>{1}</code> tiedostoa; <a href="#" id="bd_all">näytä kaikki</a></div>',
		"f_anota": "vain {0} / {1} kohdetta valittiin;\nvalitaksesi koko hakemiston, vieritä ensin loppuun",

		"f_dls": 'nykyisen hakemiston tiedostolinkit on\nvaihdettu latauslinkeiksi',

		"f_partial": "Ladataksesi turvallisesti tiedoston joka on parhaillaan latautumassa, klikkaa tiedostoa jolla on sama nimi mutta ilman <code>.PARTIAL</code> päätettä. Paina PERUUTA tai Escape tehdäksesi tämän.\n\nOK / Enter painaminen sivuuttaa tämän varoituksen ja jatkaa <code>.PARTIAL</code> väliaikaistiedoston lataamista, mikä todennäköisesti antaa sinulle vioittunutta dataa.",

		"ft_paste": "liitä {0} kohdetta$NPikanäppäin: ctrl-V",
		"fr_eperm": 'ei voida nimetä uudelleen:\nsinulla ei ole “move”-oikeutta tässä hakemistossa',
		"fd_eperm": 'ei voida poistaa:\nsinulla ei ole “delete” oikeutta tässä hakemistossa',
		"fc_eperm": 'ei voida leikata:\nsinulla ei ole “move” oikeutta tässä hakemistossa',
		"fp_eperm": 'ei voida liittää:\nsinulla ei ole “write” oikeutta tässä hakemistossa',
		"fr_emore": "valitse vähintään yksi kohde uudelleennimettäväksi",
		"fd_emore": "valitse vähintään yksi kohde poistettavaksi",
		"fc_emore": "valitse vähintään yksi kohde leikattavaksi",
		"fcp_emore": "valitse vähintään yksi kohde kopioitavaksi leikepöydälle",

		"fs_sc": "jaa hakemisto jossa olet",
		"fs_ss": "jaa valitut tiedostot",
		"fs_just1d": "et voi valita useampaa kuin yhtä,\ntai sekoittaa tiedostoja ja hakemistoja yhdessä valinnassa",
		"fs_abrt": "❌ keskeytä",
		"fs_rand": "🎲 joku.nimi",
		"fs_go": "✅ luo share",
		"fs_name": "nimi",
		"fs_src": "lähde",
		"fs_pwd": "salasana",
		"fs_exp": "vanheneminen",
		"fs_tmin": "min",
		"fs_thrs": "tuntia",
		"fs_tdays": "päivää",
		"fs_never": "ikuinen",
		"fs_pname": "valinnainen linkin nimi; on satunnainen jos tyhjä",
		"fs_tsrc": "jaettava tiedosto tai hakemisto",
		"fs_ppwd": "valinnainen salasana",
		"fs_w8": "luodaan sharea...",
		"fs_ok": "paina <code>Enter/OK</code> lisätäksesi leikepöydälle\npaina <code>ESC/Peruuta</code> sulkeaksesi",

		"frt_dec": "saattaa korjata joitakin rikkinäisiä tiedostonimiä\">url-decode",
		"frt_rst": "palauta muokatut tiedostonimet takaisin alkuperäisiksi\">↺ palauta",
		"frt_abrt": "keskeytä ja sulje tämä ikkuna\">❌ peruuta",
		"frb_apply": "UUDELLEENNIMEÄ",
		"fr_adv": "erä / liitännäistiedot / kaava uudelleennimeäminen\">lisäasetukset",
		"fr_case": "isot ja pienet kirjaimet erottava regex\">kirjainkoko",
		"fr_win": "windows-yhteensopivat nimet; korvaa <code>&lt;&gt;:&quot;\\|?*</code> japanilaisilla leveillä merkeillä\">win",
		"fr_slash": "korvaa <code>/</code> merkillä joka ei aiheuta uusien hakemistoiden luomista\">ei /",
		"fr_re": "regex hakukuvio jota käytetään alkuperäisiin tiedostonimiin; kaappausryhmiin voi viitata alla olevassa muotoilukentässä kuten &lt;code&gt;(1)&lt;/code&gt; ja &lt;code&gt;(2)&lt;/code&gt; ja niin edelleen",
		"fr_fmt": "foobar2000 innoittama:$N&lt;code&gt;(title)&lt;/code&gt; korvataan kappaleen nimellä,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; sivuuttaa [tämän] osan jos artisti on tyhjä$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; ",
		"fr_pdel": "poista",
		"fr_pnew": "tallenna nimellä",
		"fr_pname": "anna nimi uudelle esiasetuksellesi",
		"fr_aborted": "keskeytetty",
		"fr_lold": "vanha nimi",
		"fr_lnew": "uusi nimi",
		"fr_tags": "valittujen tiedostojen tagit (vain luku, viitetarkoituksiin):",
		"fr_busy": "nimetään uudelleen {0} kohdetta...\n\n{1}",
		"fr_efail": "uudelleennimeäminen epäonnistui:\n",
		"fr_nchg": "{0} uusista nimistä muutettiin <code>win</code> ja/tai <code>ei /</code> vuoksi\n\nJatketaanko näillä muutetuilla uusilla nimillä?",

		"fd_ok": "poisto OK",
		"fd_err": "poisto epäonnistui:\n",
		"fd_none": "mitään ei poistettu; ehkä palvelimen asetukset estivät (xbd)?",
		"fd_busy": "poistetaan {0} kohdetta...\n\n{1}",
		"fd_warn1": "POISTA nämä {0} kohdetta?",
		"fd_warn2": "<b>Viimeinen varoitus!</b> Haluatko varmasti poistaa?",

		"fc_ok": "siirettiin {0} kohdetta leikepöydälle",
		"fc_warn": 'siirettiin {0} kohdetta leikepöydälle\n\nmutta: vain <b>tämä</b> selain-välilehti voi liittää ne\n(koska valinta on niin valtavan suuri)',

		"fcc_ok": "kopioitiin {0} kohdetta leikepöydälle",
		"fcc_warn": 'kopioitiin {0} kohdetta leikepöydälle\n\nmutta: vain <b>tämä</b> selain-välilehti voi liittää ne\n(koska valinta on niin valtavan suuri)',

		"fp_apply": "käytä näitä nimiä",
		"fp_ecut": "leikkaa tai kopioi ensin joitakin tiedostoja / hakemistoja liitettäväksi / siirrettäväksi\n\nhuom: voit leikata / liittää eri selain-välilehtien välillä",
		"fp_ename": "{0} kohdetta ei voida siirtää tänne koska nimet ovat jo käytössä. Anna niille uudet nimet alla jatkaaksesi, tai tyhjennä nimi ohittaaksesi ne:",
		"fcp_ename": "{0} kohdetta ei voida kopioida tänne koska nimet ovat jo käytössä. Anna niille uudet nimet alla jatkaaksesi, tai tyhjennä nimi ohittaaksesi ne:",
		"fp_emore": "tiedostonimien törmäyksiä on vielä korjaamatta",
		"fp_ok": "siirto OK",
		"fcp_ok": "kopiointi OK",
		"fp_busy": "siirretään {0} kohdetta...\n\n{1}",
		"fcp_busy": "kopioidaan {0} kohdetta...\n\n{1}",
		"fp_abrt": "keskeytetään...", //m
		"fp_err": "siirto epäonnistui:\n",
		"fcp_err": "kopiointi epäonnistui:\n",
		"fp_confirm": "siirrä nämä {0} kohdetta tänne?",
		"fcp_confirm": "kopioi nämä {0} kohdetta tänne?",
		"fp_etab": 'leikepöydän lukeminen toisesta selain-välilehdestä epäonnistui',
		"fp_name": "ladataan tiedostoa laitteeltasi. Anna sille nimi:",
		"fp_both_m": '<h6>valitse mitä liittää</h6><code>Enter</code> = Siirrä {0} tiedostoa kohteesta «{1}»\n<code>ESC</code> = Lataa {2} tiedostoa laitteeltasi',
		"fcp_both_m": '<h6>valitse mitä liittää</h6><code>Enter</code> = Kopioi {0} tiedostoa kohteesta «{1}»\n<code>ESC</code> = Lataa {2} tiedostoa laitteeltasi',
		"fp_both_b": '<a href="#" id="modal-ok">Siirrä</a><a href="#" id="modal-ng">Lähetä</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopioi</a><a href="#" id="modal-ng">Lähetä</a>',

		"mk_noname": "kirjoita nimi vasemmalla olevaan tekstikenttään ennen kuin teet tuon :p",

		"tv_load": "Ladataan tekstidokumenttia:\n\n{0}\n\n{1}% ({2} / {3} Mt ladattu)",
		"tv_xe1": "tekstitiedoston lataaminen epäonnistui:\n\nvirhe ",
		"tv_xe2": "404, tiedostoa ei löydy",
		"tv_lst": "tekstitiedostojen lista hakemistossa",
		"tvt_close": "palaa hakemistonäkymään$NPikanäppäin: M (tai Esc)\">❌ sulje",
		"tvt_dl": "lataa tämä tiedosto$NPikanäppäin: Y\">💾 lataa",
		"tvt_prev": "näytä edellinen dokumentti$NPikanäppäin: i\">⬆ edell",
		"tvt_next": "näytä seuraava dokumentti$NPikanäppäin: K\">⬇ seur",
		"tvt_sel": "valitse tiedosto &nbsp; ( leikkausta / kopiointia / poistoa / ... varten )$NPikanäppäin: S\">val",
		"tvt_edit": "avaa tiedosto tekstieditorissa$NPikanäppäin: E\">✏️ muokkaa",
		"tvt_tail": "seuraa tiedoston muutoksia; näytä uudet rivit reaaliaikaisesti\">📡 seuraa",
		"tvt_wrap": "rivitys\">↵",
		"tvt_atail": "lukitse vieritys sivun alaosaan\">⚓",
		"tvt_ctail": "dekoodaa terminaalin värit (ansi escape koodit)\">🌈",
		"tvt_ntail": "vieritysbufferin raja (kuinka monta tavua tekstiä pidetään ladattuna)",

		"m3u_add1": "kappale lisätty m3u soittolistaan",
		"m3u_addn": "{0} kappaletta lisätty m3u soittolistaan",
		"m3u_clip": "m3u soittolista nyt kopioitu leikepöydälle\n\nsinun tulisi luoda uusi tekstitiedosto nimeltä jotain.m3u ja liittää soittolista siihen dokumenttiin; tämä tekee siitä soitettavan",

		"gt_vau": "älä näytä videoita, toista vain ääni\">🎧",
		"gt_msel": "aktivoi tiedostonvalintatila; ctrl-klikkaa ohittaaksesi valitsemisen väliaikaisesti$N$N&lt;em&gt;tuplaklikkaa tiedostoa / hakemistoa avataksesi sen&lt;/em&gt;$N$NPikanäppäin: S\">valitsin",
		"gt_crop": "rajaa pienoiskuvat keskeltä\">rajaa",
		"gt_3x": "korkearesoluutioiset pienoiskuvat\">3x",
		"gt_zoom": "zoomaa",
		"gt_chop": "pilko",
		"gt_sort": "järjestä",
		"gt_name": "nimi",
		"gt_sz": "koko",
		"gt_ts": "päiväys",
		"gt_ext": "tyyppi",
		"gt_c1": "rajaa tiedostonimiä enemmän (näytä vähemmän)",
		"gt_c2": "rajaa tiedostonimiä vähemmän (näytä enemmän)",

		"sm_w8": "haetaan...",
		"sm_prev": "alla olevat hakutulokset ovat edellisestä hausta:\n  ",
		"sl_close": "sulje hakutulokset",
		"sl_hits": "näytetään {0} osumaa",
		"sl_moar": "lataa lisää",

		"s_sz": "koko",
		"s_dt": "päiväys",
		"s_rd": "polku",
		"s_fn": "nimi",
		"s_ta": "tagit",
		"s_ua": "ylös@",
		"s_ad": "edist.",
		"s_s1": "minimi Mt",
		"s_s2": "maksimi Mt",
		"s_d1": "min. iso8601",
		"s_d2": "maks. iso8601",
		"s_u1": "ladattu jälkeen",
		"s_u2": "ja/tai ennen",
		"s_r1": "polku sisältää &nbsp; (välilyönnillä erotetuttuina)",
		"s_f1": "nimi sisältää &nbsp; (negatoi käyttämällä -nope)",
		"s_t1": "tagit sisältää &nbsp; (^=alku, loppu=$)",
		"s_a1": "tietyt metadatan ominaisuudet",

		"md_eshow": "ei voida renderoida ",
		"md_off": "[📜<em>readme</em>] poistettu käytöstä [⚙️] -- dokumentti piilotettu",

		"badreply": "Palvelimen vastauksen jäsentäminen epäonnistui.",

		"xhr403": "403: Pääsy kielletty\n\nkokeile painaa F5, ehkä sinut kirjattiin ulos",
		"xhr0": "tuntematon (todennäköisesti yhteys palvelimeen katosi, tai palvelin on pois päältä)",
		"cf_ok": "sori siitä -- DD" + wah + "oS suojaus aktivoitui\n\nasioiden pitäisi jatkua noin 30 sekunnissa\n\njos mitään ei tapahdu, paina F5 ladataksesi sivun uudelleen",
		"tl_xe1": "alihakemistojen listaaminen epäonnistui:\n\nvirhe ",
		"tl_xe2": "404: hakemistoa ei löydy",
		"fl_xe1": "hakemiston tiedostojen listaaminen epäonnistui:\n\nvirhe ",
		"fl_xe2": "404: hakemistoa ei löydy",
		"fd_xe1": "alihakemiston luominen epäonnistui:\n\nvirhe ",
		"fd_xe2": "404: Ylähakemistoa ei löydy",
		"fsm_xe1": "viestin lähettäminen epäonnistui:\n\nvirhe ",
		"fsm_xe2": "404: Ylähakemistoa ei löydy",
		"fu_xe1": "unpost-listan lataaminen palvelimelta epäonnistui:\n\nvirhe ",
		"fu_xe2": "404: Tiedostoa ei löydy??",

		"fz_tar": "pakkaamaton gnu-tar tiedosto (linux / mac)",
		"fz_pax": "pakkaamaton pax-formaatin tar (hitaampi)",
		"fz_targz": "gnu-tar gzip tason 3 pakkauksella$N$Nyleensä hyvin hidas, $Nkäytä pakkamatonta tar:ia tämän sijasta",
		"fz_tarxz": "gnu-tar xz tason 1 pakkauksella$N$Nyleensä hyvin hidas, $Nkäytä pakkamatonta tar:ia tämän sijasta",
		"fz_zip8": "zip utf8-tiedostonimillä (suattaapi olla epävakaa windows 7:ssa ja vanhemmissa)",
		"fz_zipd": "zip perinteisillä cp437 tiedostonimillä esihistoriallisille ohjelmistoille",
		"fz_zipc": "cp437, jossa crc32 laskettu aikaisin,$NMS-DOS PKZIP v2.04g:lle (lokakuu 1993)$N(kestää kauemmin käsitellä ennen latauksen alkua)",

		"un_m1": "voit poistaa tuoreet tai keskeyttää keskeneräiset latauksesi alta",
		"un_upd": "päivitä",
		"un_m4": "tai jakaa alla näkyvät tiedostot:",
		"un_ulist": "näytä",
		"un_ucopy": "kopioi",
		"un_flt": "valinnainen suodatin:&nbsp; URL:n täytyy sisältää",
		"un_fclr": "tyhjennä suodatin",
		"un_derr": 'unpost-poisto epäonnistui:\n',
		"un_f5": 'jotain hajosi, kokeile päivitystä tai paina F5',
		"un_uf5": "pahoittelen mutta sinun täytyy päivittää sivu (esimerkiksi painamalla F5 tai CTRL-R) ennen kuin tämä lataus voidaan keskeyttää",
		"un_nou": '<b>huom!</b> palvelin liian kiireinen näyttääkseen keskeneräiset lataukset; klikkaa "päivitä" linkkiä hetken kuluttua',
		"un_noc": '<b>huom!</b> täysin ladattujen tiedostojen unpost ei ole käytössä/sallittu palvelimen asetuksissa',
		"un_max": "näytetään ensimmäiset 2000 tiedostoa (käytä suodatinta)",
		"un_avail": "{0} viimeaikaista latausta voidaan poistaa<br />{1} keskeneräistä voidaan keskeyttää",
		"un_m2": "järjestetty latausajan mukaan; viimeisimmät ensin:",
		"un_no1": "hupsis! yksikään lataus ei ole riittävän tuore",
		"un_no2": "hupsis! yksikään tuota suodatinta vastaava lataus ei ole riittävän tuore",
		"un_next": "poista seuraavat {0} tiedostoa alla",
		"un_abrt": "keskeytä",
		"un_del": "poista",
		"un_m3": "ladataan viimeaikana lähettämiäsi tiedostoja...",
		"un_busy": "poistetaan {0} tiedostoa...",
		"un_clip": "{0} linkkiä kopioitu leikepöydälle",

		"u_https1": "sinun kannattaisi",
		"u_https2": "vaihtaa https:ään",
		"u_https3": "paremman suorituskyvyn vuoksi",
		"u_ancient": 'selaimesi on ns. vaikuttavan ikivanha --  kannattais varmaan <a href="#" onclick="goto(\'bup\')">käyttää bup:ia tän sijaan</a>',
		"u_nowork": "tarvitaan firefox 53+ tai chrome 57+ tai iOS 11+",
		"tail_2old": "tarvitaan firefox 105+ tai chrome 71+ tai iOS 14.5+",
		"u_nodrop": 'selaimesi on liian vanha vedä-ja-pudota lataamiseen',
		"u_notdir": "tuo ei ole hakemisto!\n\nselaimesi on liian vanha,\nkokeile sen sijaan 'vedä-pudota'-tekniikkaa.",
		"u_uri": "'vedä-pudottaaksesi' kuvia muista selainikkunoista,\npudota se isoon latausnapppiin",
		"u_enpot": 'vaihda <a href="#">peruna UI:hin</a> (voi parantaa latausnopeutta)',
		"u_depot": 'vaihda <a href="#">ylelliseen UI:hin</a> (voi vähentää latausnopeutta)',
		"u_gotpot": 'vaihdetaan peruna UI:hin paremman latausnopeuden vuoksi,\n\ntee miten lystäät, jos ei kelpaa!',
		"u_pott": "<p>tiedostot: &nbsp; <b>{0}</b> valmis, &nbsp; <b>{1}</b> epäonnistui, &nbsp; <b>{2}</b> kiireinen, &nbsp; <b>{3}</b> jonossa</p>",
		"u_ever": "tämä on peruslatain; up2k tarvitsee vähintään<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'peruslatain; <a href="#" id="u2yea">up2k</a> on parempi',
		"u_uput": 'optimoi latausnopeus (älä laske tarkistussummia)',
		"u_ewrite": 'sinulla ei ole move-oikeutta tähän hakemistoon',
		"u_eread": 'sinulla ei ole read-oikeutta tähän hakemistoon',
		"u_enoi": 'tiedostohaku ei ole käytössä palvelimen asetuksissa',
		"u_enoow": "ylikirjoitus ei toimi täällä; tarvitaan “Delete”-oikeus",
		"u_badf": 'Nämä {0} tiedostoa ({1} yhteensä) ohitettiin, mahdollisesti tiedostojärjestelmän oikeuksien vuoksi:\n\n',
		"u_blankf": 'Nämä {0} tiedostoa ({1} yhteensä) ovat tyhjiä; ladataanko ne silti?\n\n',
		"u_applef": 'Nämä {0} tiedostoa ({1} yhteensä) ovat todennäköisesti ei-toivottuja;\nPaina <code>OK/Enter</code> OHITTAAKSESI seuraavat tiedostot,\nPaina <code>Peruuta/ESC</code> jos ET halua sulkea pois, ja LATAA nekin:\n\n',
		"u_just1": '\nEhkä toimii paremmin jos valitset vain yhden tiedoston',
		"u_ff_many": "jos käytät <b>Linux / MacOS / Android,</b> niin tämä määrä tiedostoja <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>saattaa</em> kaataa Firefoxin!</a>\njos niin käy, kokeile uudelleen (tai käytä Chromea).",
		"u_up_life": "Tämä lataus poistetaan palvelimelta\n{0} sen valmistumisen jälkeen",
		"u_asku": 'lataa nämä {0} tiedostoa kohteeseen <code>{1}</code>',
		"u_unpt": "voit perua / poistaa tämän latauksen käyttämällä vasemmalla ylhäällä olevaa 🧯",
		"u_bigtab": 'näytetään {0} tiedostoa\n\ntämä voi kaataa selaimesi, oletko varma?',
		"u_scan": 'Skannataan tiedostoja...',
		"u_dirstuck": 'hakemistoiteraattori jumittui yrittäessään käyttää seuraavia {0} kohdetta; ohitetaan:',
		"u_etadone": 'Valmis ({0}, {1} tiedostoa)',
		"u_etaprep": '(valmistellaan latausta)',
		"u_hashdone": 'hajautus valmis',
		"u_hashing": 'hajautus',
		"u_hs": 'kätellään...',
		"u_started": "tiedostoja ladataan nyt; tsekkaa [🚀]",
		"u_dupdefer": "duplikaatti; käsitellään kaikkien muiden tiedostojen jälkeen",
		"u_actx": "klikkaa tätä tekstiä estääksesi suorituskyvyn<br />heikkenemisen vaihtaessasi muihin ikkunoihin/välilehtiin",
		"u_fixed": "OK!&nbsp; Hommat hoidossa 👍",
		"u_cuerr": "chunk {0} / {1} lataus epäonnistui;\ntuskin haittaa, jatketaan\n\ntiedosto: {2}",
		"u_cuerr2": "palvelin hylkäsi latauksen (chunk {0} / {1});\nyritetään myöhemmin uudelleen\n\ntiedosto: {2}\n\nvirhe ",
		"u_ehstmp": "yritetään uudelleen; katso oikealta alhaalta",
		"u_ehsfin": "palvelin hylkäsi pyynnön viimeistellä lataus; yritetään uudelleen...",
		"u_ehssrch": "palvelin hylkäsi pyynnön suorittaa haku; yritetään uudelleen...",
		"u_ehsinit": "palvelin hylkäsi pyynnön aloittaa lataus; yritetään uudelleen...",
		"u_eneths": "verkkovirhe latauksen kättelyssä; yritetään uudelleen...",
		"u_enethd": "verkkovirhe kohteen olemassaolon testauksessa; yritetään uudelleen...",
		"u_cbusy": "odotetaan palvelimen luottavan meihin taas verkko-ongelman jälkeen...",
		"u_ehsdf": "palvelimen levytila loppui!\n\nyritetään jatkuvasti, siinä tapauksessa että joku\nvapauttaa tarpeeksi tilaa jatkamiseen",
		"u_emtleak1": "näyttää siltä että selaimessasi saattaa olla muistivuoto;\nole hyvä ja",
		"u_emtleak2": ' <a href="{0}">vaihda https:ään (suositeltu)</a> tai ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'kokeile seuraavaa:\n<ul><li>paina <code>F5</code> päivittääksesi sivun</li><li>sitten poista käytöstä &nbsp;<code>mt</code>&nbsp; nappi &nbsp;<code>⚙️ asetuksissa</code></li><li>ja kokeile latausta uudelleen</li></ul>Lataukset ovat hieman hitaampia, minkäs teet.\nSori siitä!\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">sisältää bugfixin tätä varten</a>',
		"u_emtleakf": 'kokeile seuraavaa:\n<ul><li>paina <code>F5</code> päivittääksesi sivun</li><li>sitten ota käyttöön <code>🥔</code> (peruna) lataus UI:ssa<li>ja kokeile latausta uudelleen</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">toivottavasti saa kerättyä itsensä kasaan</a> jossain vaiheessa',
		"u_s404": "ei löydy palvelimelta",
		"u_expl": "selitä",
		"u_maxconn": "useimmat selaimet rajoittavat tämän 6:een, mutta firefox antaa nostaa sitä <code>connections-per-server</code> asetuksella <code>about:config</code>:issa",
		"u_tu": '<p class="warn">VAROITUS: turbo päällä, <span>&nbsp;asiakasohjelma ei välttämättä huomaa jatkaa keskeneräisiä latauksia; katso turbo-napin vihje</span></p>',
		"u_ts": '<p class="warn">VAROITUS: turbo päällä, <span>&nbsp;hakutulokset voivat olla vääriä; katso turbo-napin vihje</span></p>',
		"u_turbo_c": "turbo on poistettu käytöstä palvelimen asetuksissa",
		"u_turbo_g": "poistetaan turbo käytöstä koska sinulla ei ole\nhakemistolistausoikeuksia tässä asemassa",
		"u_life_cfg": 'automaattinen poisto <input id="lifem" p="60" /> min kuluttua (tai <input id="lifeh" p="3600" /> tuntia)',
		"u_life_est": 'lataus poistetaan <span id="lifew" tt="paikallinen aika">---</span>',
		"u_life_max": 'tämä hakemisto pakottaa\nmaksimi elinajan {0}',
		"u_unp_ok": 'unpost on sallittu {0}',
		"u_unp_ng": 'unpost EI ole sallittu',
		"ue_ro": 'sinulla on vain read-oikeus tähän hakemistoon\n\n',
		"ue_nl": 'et ole tällä hetkellä kirjautunut sisään',
		"ue_la": 'olet tällä hetkellä kirjautunut sisään nimellä "{0}"',
		"ue_sr": 'olet tällä hetkellä tiedostohaku-tilassa\n\nvaihda lataus-tilaan klikkaamalla suurennuslasia 🔎 (suuren HAKU napin vieressä), ja yritä latausta uudelleen\n\npahoittelen',
		"ue_ta": 'yritä latausta uudelleen, sen pitäisi toimia nyt',
		"ue_ab": "tätä tiedostoa ladataan jo toiseen hakemistoon, ja se lataus täytyy suorittaa loppuun ennen kuin tiedostoa voidaan ladata muualle.\n\nVoit keskeyttää ja unohtaa alkuperäisen latauksen käyttämällä vasemmalla ylhäällä olevaa 🧯",
		"ur_1uo": "OK: Tiedosto ladattu onnistuneesti",
		"ur_auo": "OK: Kaikki {0} tiedostoa ladattu onnistuneesti",
		"ur_1so": "OK: Tiedosto löytyi palvelimelta",
		"ur_aso": "OK: Kaikki {0} tiedostoa löytyi palvelimelta",
		"ur_1un": "Lataus epäonnistui, pahoittelen",
		"ur_aun": "Kaikki {0} latausta epäonnistui, pahoittelen",
		"ur_1sn": "Tiedostoa EI löytynyt palvelimelta",
		"ur_asn": "{0} tiedostoa EI löytynyt palvelimelta",
		"ur_um": "Valmis;\n{0} latausta OK,\n{1} latausta epäonnistui, pahoittelen",
		"ur_sm": "Valmis;\n{0} tiedostoa löytyi palvelimelta,\n{1} tiedostoa EI löytynyt palvelimelta",

		"lang_set": "ladataanko sivu uudestaan kielen vaihtamiseksi?",
	},
	"fra": {
		"tt": "français",

		"cols": {
			"c": "bouton d'action",
			"dur": "durée",
			"q": "qualité / débit binaire",
			"Ac": "codec audio",
			"Vc": "codec vidéo",
			"Fmt": "format / conteneur",
			"Ahash": "somme de contrôle audio",
			"Vhash": "somme de contrôle vidéo",
			"Res": "résolution",
			"T": "type de fichier",
			"aq": "qualité audio / débit binaire",
			"vq": "qualité vidéo / débit binaire",
			"pixfmt": "sous-échantillonnage / structure de pixel",
			"resw": "résolution horizontale",
			"resh": "résolution verticale",
			"chs": "canaux audio",
			"hz": "fréquence"
		},

		"hks": [
			[
				"misc",
				["Échap", "ferme divers menus"],

				"gestionaire de fichiers",
				["G", "activer vue en liste / vue en grille"],
				["T", "activer les miniatures / icônes"],
				["⇧ A/D", "taille des miniatures"],
				["ctrl-K", "suprimer la sélection"],
				["ctrl-X", "couper la sélection au presse-papier"],
				["ctrl-C", "copier la sélection au presse-papier"],
				["ctrl-V", "coller (déplacer/copier) ici"],
				["Y", "télécharger la sélection"],
				["F2", "renomer la sélection"],

				"file-list-sel",
				["Espace", "activer la sélection de fichiers"],
				["↑/↓", "déplacer le selecteur"],
				["ctrl ↑/↓", "déplacer le curseur et la zone d'affichage"],
				["⇧ ↑/↓", "sélectioner le fichier précédent/suivant"],
				["ctrl-A", "sélectionner tout les fichiers / dossiers"],
			], [
				"navigation",
				["B", "basculer la vue en fil d'Ariane / panneau de navigation"],
				["I/K", "dossier précédent/suivant"],
				["M", "dossier parent (ou réduire le dossier actuel)"],
				["V", "activer les dossiers / fichiers texte dans le volet de navigation"],
				["A/D", "taille du volet de navigation"],
			], [
				"lecteur-audio",
				["J/L", "chanson précédente/suivante"],
				["U/O", "sauter 10s en arrière/avant"],
				["0..9", "sauter à 0%..90%"],
				["P", "lecture/pause (démarre également la lecture)"],
				["S", "sélectionner la chanson en cours"],
				["Y", "télécharger le morceau"],
			], [
				"visionneuse d'image",
				["J/L, ←/→", "image précédente/suivante"],
				["Début/Fin, ⭦/Fin", "première/dernière image"],
				["F", "plein écran"],
				["R", "rotation horaire"],
				["⇧ R", "rotation antihoraire"],
				["S", "sélectionner l'image"],
				["Y", "télécharger l'image"],
			], [
				"lecteur vidéo",
				["U/O", "sauter 10s en arrière/avant"],
				["P/K/Espace", "lecture/pause"],
				["C", "continuer de lire la suivante"],
				["V", "lire en boucle"],
				["M", "couper le son"],
				["[ and ]", "définir l'intervalle de boucle"],
			], [
				"visionneuse de texte",
				["I/K", "fichier précédent/suivant"],
				["M", "fermer le fichier texte"],
				["E", "modifier le fichier texte"],
				["S", "sélectioner le fichier (pour le couper/copier/renommer)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Annuler",

		"enable": "Activer",
		"danger": "DANGER",
		"clipped": "copié dans le presse-papier",

		"ht_s1": "seconde",
		"ht_s2": "secondes",
		"ht_m1": "minute",
		"ht_m2": "minutes",
		"ht_h1": "heure",
		"ht_h2": "heures",
		"ht_d1": "jour",
		"ht_d2": "jours",
		"ht_and": " et ",

		"goh": "panneau-de-commande",
		"gop": 'élément "frère" précédent">précédent',
		"gou": 'dossier parent">haut',
		"gon": 'dossier suivant">suivant',
		"logout": "Déconnexion ",
		"login": "Se connecter", //m
		"access": " accès",
		"ot_close": "fermer le sous-menu",
		"ot_search": "chercher des fichiers par leurs attributs, chemin / nom, tag musicaux, ou nimporte quelle combinaison de ces options$N$N&lt;code&gt;foo bar&lt;/code&gt; = doit contenir à la fois «foo» et «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = doit contenir «foo» mais pas «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = commence par «yana» et est un fichier «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = contient exactement «try unite»$N$Nle format de date est iso-8601, comme$N&lt;code&gt;2009-12-31&lt;/code&gt; ou &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: supprimer vos téléchargements récents, ou annuler ceux en cours",
		"ot_bup": "bup: téléverseur de base, prend même en charge netscape 4.0",
		"ot_mkdir": "mkdir: créer un nouveau répertoire",
		"ot_md": "new-md: créer un nouveau document markdown",
		"ot_msg": "msg: envoyer un message au journal du serveur",
		"ot_mp": "options du lecteur multimedia",
		"ot_cfg": "options de configuration",
		"ot_u2i": 'up2k : téléverser des fichiers (si vous avez un accès en écriture) ou basculer en mode recherche pour voir s\'ils existent quelque part sur le serveur$N$Nles téléversements peuvent être repris, ils sont multithreadé, et les horodatages des fichiers sont préservés, mais cela utilise plus de CPU que [🎈]&nbsp; (le téléverseur de base)<br /><br />pendant les téléversements, cette icône devient un indicateur de progression!',
		"ot_u2w": 'up2k : téléverser des fichiers avec prise en charge de la reprise (fermez votre navigateur et déposez les mêmes fichiers plus tard)$N$multithreadé, et les horodatages des fichiers sont préservés, mais cela utilise plus de CPU que [🎈]&nbsp; (le téléverseur de base)<br /><br />pendant les téléversements, cette icône devient un indicateur de progression!',
		"ot_noie": 'Utilisez Chrome / Firefox / Edge',

		"ab_mkdir": "créer un nouveau répertoire",
		"ab_mkdoc": "faire un nouveau document markdown",
		"ab_msg": "envoyer un message au journal du serveur",

		"ay_path": "passer aux dossiers",
		"ay_files": "passer aux fichiers",

		"wt_ren": "renommer les éléments sélectionnés$NHotkey: F2",
		"wt_del": "supprimer les éléments sélectionnés$NHotkey: ctrl-K",
		"wt_cut": "couper les éléments sélectionnés &lt;small&gt;(puis coller ailleurs)&lt;/small&gt;$NHotkey: ctrl-X",
		"wt_cpy": "copier les éléments sélectionnés dans le presse-papiers$N(pour les coller ailleurs)$NHotkey: ctrl-C",
		"wt_pst": "coller une sélection précédemment coupée / copiée$NHotkey: ctrl-V",
		"wt_selall": "sélectionner tous les fichiers$NHotkey: ctrl-A (lorsque le fichier est sélectionné)",
		"wt_selinv": "inverser la sélection",
		"wt_zip1": "télécharger ce dossier en tant qu'archive",
		"wt_selzip": "télécharger la sélection en tant qu'archive",
		"wt_seldl": "télécharger la sélection en tant que fichiers séparés$NHotkey: Y",
		"wt_npirc": "copier les informations de la musique au format irc",
		"wt_nptxt": "copier les informations de la musique en texte brut",
		"wt_m3ua": "ajouter à la playlist m3u (cliquez sur <code>📻copier</code> plus tard)",
		"wt_m3uc": "copier la playlist m3u dans le presse-papiers",
		"wt_grid": "basculer entre la vue en grille / liste$NHotkey: G",
		"wt_prev": "musique précédente$NHotkey: J",
		"wt_play": "lecture / pause$NHotkey: P",
		"wt_next": "musique suivante$NHotkey: L",

		"ul_par": "téléversements parallèles:",
		"ut_rand": "attribution de noms de fichiers aléatoires",
		"ut_u2ts": "copier l'horodatage de dernière modification$Nde votre système de fichiers vers le serveur\">📅",
		"ut_ow": "écraser les fichiers existants sur le serveur?$N🛡️: jamais (générera un nouveau nom de fichier à la place)$N🕒: écraser si le fichier sur le serveur est plus ancien que le vôtre$N♻️: toujours écraser si les fichiers sont différents",
		"ut_mt": "continuer à calculer la somme de contrôle d'autres fichiers pendant le téléversement$N$Npeut-être désactiver si votre CPU ou HDD est la cause de perte de performances",
		"ut_ask": 'demander confirmation avant le début du téléversement">💭',
		"ut_pot": "améliorer la vitesse de téléversement sur les appareils lents$Nen simplifiant l'interface utilisateur",
		"ut_srch": "ne pas réellement téléverser, mais vérifier si les fichiers existent déjà$N sur le serveur (scannera tous les dossiers que vous pouvez lire)",
		"ut_par": "mettre en pause les téléversements en le réglant sur 0$N$Naugmenter si votre connexion est lente / à forte latence$N$Nle garder à 1 sur le LAN ou si le HDD du serveur est un goulot d'étranglement",
		"ul_btn": "déposer des fichiers / dossiers<br>ici (ou cliquez sur moi)",
		"ul_btnu": "T É L É V E R S E R",
		"ul_btns": "C H E R C H E R",

		"ul_hash": "somme de contrôle",
		"ul_send": "envoyer",
		"ul_done": "terminé",
		"ul_idle1": "aucun téléversement n'est encore dans la file d'attente",
		"ut_etah": "moyenne &lt;em&gt;hashing&lt;/em&gt; vitesse, et temps estimé jusqu'à la fin",
		"ut_etau": "moyenne &lt;em&gt;upload&lt;/em&gt; vitesse et temps estimé jusqu'à la fin",
		"ut_etat": "moyenne &lt;em&gt;total&lt;/em&gt; vitesse et temps estimé jusqu'à la fin",

		"uct_ok": "terminé avec succès",
		"uct_ng": "non réussi : échoué / rejeté / non trouvé",
		"uct_done": "terminés et échoué combinés",
		"uct_bz": "hachage ou téléversement",
		"uct_q": "inactif, en attente",

		"utl_name": "nom de fichier",
		"utl_ulist": "liste",
		"utl_ucopy": "copie",
		"utl_links": "liens",
		"utl_stat": "état",
		"utl_prog": "progrès",

		// keep short:
		"utl_404": "404",
		"utl_err": "ERREUR",
		"utl_oserr": "OS-ERREUR",
		"utl_found": "trouvé",
		"utl_defer": "état",
		"utl_yolo": "YOLO",
		"utl_done": "terminé",

		"ul_flagblk": "les fichiers ont été ajoutés à la file d'attente</b><br>cependant, il y a un processus up2k actif dans un autre onglet du navigateur,<br>en attente qu'il finisse d'abord",
		"ul_btnlk": "la configuration du serveur a verrouillé cette options dans cet état",

		"udt_up": "Téléverser",
		"udt_srch": "Chercher",
		"udt_drop": "déposer ici",

		"u_nav_m": '<h6>aight, ques-que tu à ?</h6><code>Enter</code> = Fichiers (un ou plus)\n<code>ESC</code> = Un dossier (sous-dossiers inclus)',
		"u_nav_b": '<a href="#" id="modal-ok">Fichiers</a><a href="#" id="modal-ng">Un dossier</a>',

		"cl_opts": "options",
		"cl_themes": "thème",
		"cl_langs": "langue",
		"cl_ziptype": "téléchargement de dossier",
		"cl_uopts": "up2k",
		"cl_favico": "favicon",
		"cl_bigdir": "gros dossiers",
		"cl_hsort": "#sort",
		"cl_keytype": "notation des touches",
		"cl_hiddenc": "colonnes masquées",
		"cl_hidec": "masquer",
		"cl_reset": "réinitialiser",
		"cl_hpick": "cliquez sur les en-têtes de colonnes pour les masquer dans le tableau ci-dessous",
		"cl_hcancel": "masquage des colonnes annulé",

		"ct_grid": '田 grille',
		"ct_ttips": '◔ ◡ ◔">ℹ️ infobulles',
		"ct_thumb": 'vue en grille, activer les icônes ou les miniatures$NHotkey: T">🖼️ minia',
		"ct_csel": 'utiliser CTRL et MAJ pour selectioner des fichiers en vue en grille">sel',
		"ct_ihop": 'quand le visionneuse d\'image est fermé, faire defiller vers le bas jusqu\'au dernier fichier">g⮯',
		"ct_dots": 'voir les fichiers caché (si le serveur le permet)">dotfiles',
		"ct_qdel": 'ne demander qu\'une confirmation lors de la suppression de fichiers>qdel',
		"ct_dir1st": 'trier les dossiers avant les fichiers">📁 first',
		"ct_nsort": 'triage par numérotation (pour les nom de fichiers qui sont numérotés)">nsort',
		"ct_utc": 'voir tout les horodatage en format UTC">UTC',
		"ct_readme": 'voir le fichier README.md dans le listage des dossiers">📜 readme',
		"ct_idxh": 'voir une version html (index.html) au-lieu du listage des dossiers normal">htm',
		"ct_sbars": 'montrer la barre de defilement">⟊',

		"cut_umod": "si un fichier existe déjà sur le server, mettre à jour l'horodatage de dernière modification du serveur pour qu'il corresponde à votre fichier local (nécessite des autorisations d'écriture et de suppression)\">re📅",

		"cut_turbo": "le bouton yolo, vous ne voulez probablement PAS activer ceci:$N$Nutilisez ceci si vous téléchargez une grande quantité de fichiers et que vous devez redémarrer pour une raison quelconque, et que vous souhaitez continuer le téléchargement dès que possible$N$Ncela remplace la vérification de hachage par une simple <em>&quot;est-ce que cela a la même taille de fichier sur le serveur?&quot;</em> donc si le contenu du fichier est différent, il ne sera PAS téléchargé$N$Nvous devriez désactiver cela lorsque le téléchargement est terminé, puis &quot;télécharger&quot; les mêmes fichiers à nouveau pour laisser le client les vérifier\">turbo",

		"cut_datechk": "n'a aucun effet à moins que le bouton turbo ne soit activé$N$Nréduit le facteur yolo d'un tout petit peu ; vérifie si les horodatages des fichiers sur le serveur correspondent aux vôtres$N$Ndevrait <em>théoriquement</em> attraper la plupart des téléchargements inachevés / corrompus, mais n'est pas un substitut à un passage de vérification avec turbo désactivé par la suite\">date-chk",

		"cut_u2sz": "taille (en MiB) de chaque morceau de téléversement; des grosse valeurs vont mieux passer si la distance entre le serveur et vous est trés grande. Si vous avez une connection trés instable, essayer de plus petites valeurs",

		"cut_flag": "s'assurer qu'un seul onglet est entrain de mettre un fichier en ligne a la fois $N -- les autres onglets doivent avoir cette option activé aussi $N -- affecte seulement les onglets qui sont sur le même domaine",

		"cut_az": "mettre en ligne les fichiers dans l'ordre alphabétique, plutôt que le plus petit fichier en premier$N$Nl'ordre alphabétique peut rendre la lecture plus douce sur pour les yeux si quelque chose s'est mal passé sur le serveur, mais cela rend le téléversement légèrement plus lent sur fibre / LAN",

		"cut_nag": "recevoir une notification via l'OS quand un téléversement finit$N(seulement si le navigateur ou l'onglet n'est pas actif)",
		"cut_sfx": "alerte audible quand le téléversement finit$N(seulement si le navigateur ou l'onglet n'est pas actif)",

		"cut_mt": "utiliser le calcul de somme de contrôle multithreadé pour accelerer le processus$N$Ncela utilise des web-workers et nécessite$Nplus de RAM (jusqu'à 512 MiB supplémentaires)$N$NCela rend https 30% plus rapide, http 4.5x plus rapide\">mt",

		"cut_wasm": "utiliser wasm au lieu du hachage intégré du navigateur; améliore la vitesse sur les navigateurs basés sur chrome mais augmente la charge CPU, et de nombreuses anciennes versions de chrome ont des bugs qui font que le navigateur consomme toute la RAM et plante si cela est activé\">wasm",

		"cft_text": "text favicon (laisser vide et rafraîchir pour désactiver)",
		"cft_fg": "couleur de premier plan",
		"cft_bg": "couleur d'arrière-plan",

		"cdt_lim": "nombre maximum de fichiers à afficher dans un dossier",
		"cdt_ask": "lorsque vous faites défiler vers le bas,$Nau lieu de charger plus de fichiers,$Ndemander quoi faire",
		"cdt_hsort": "combien de règles de tri (&lt;code&gt;,sorthref&lt;/code&gt;) à inclure dans les media-URLs. Définir cette valeur à 0 ignorera également les règles de tri incluses dans les liens média lorsque vous cliquez dessus.",

		"tt_entree": "afficher le panneau de navigation (arborescence des dossiers)$NHotkey: B",
		"tt_detree": "afficher le fil d’Ariane$NHotkey: B",
		"tt_visdir": "faire défiler jusqu'au dossier sélectionné",
		"tt_ftree": "basculer l'arborescence des dossiers / fichiers texte$NHotkey: V",
		"tt_pdock": "afficher les dossiers parents dans un panneau ancré en haut",
		"tt_dynt": "croissance automatique à mesure que l'arborescence s'étend",
		"tt_wrap": "retour à la ligne",
		"tt_hover": "révéler les lignes débordantes au survol$N( interrompt le défilement à moins que le curseur de la souris ne soit dans la gouttière gauche )",

		"ml_pmode": "à la fin du dossier…",
		"ml_btns": "cmds",
		"ml_tcode": "transcoder",
		"ml_tcode2": "transcoder vers",
		"ml_tint": "teinte",
		"ml_eq": "égaliseur audio",
		"ml_drc": "compresseur de plage dynamique",

		"mt_loop": "répéter en boucle une musique\">🔁",
		"mt_one": "stopper après une musique\">1️⃣",
		"mt_shuf": "mélanger les musiques dans chaque dossiers\">🔀",
		"mt_aplay": "jouer automatiquement si le lien utilisé pour accéder au serveur a un song-ID $N$N, désactiver cela arrêtera également la mise à jour de l'URL de la page avec les song-IDs lors de la lecture de la musique, pour éviter la lecture automatique si ces paramètres sont perdus mais que l'URL reste\">a▶",
		"mt_preload": "commencer à charger la prochaine chanson près de la fin pour une lecture sans interruption\">preload",
		"mt_prescan": "explorer le dossier suivant avant la dernière musique$Nne finisse, pour garder le navigateur content$Npour qu'il n'arrête pas la lecture\">nav",
		"mt_fullpre": "essayer de pré-charger la musique entière;$N✅ activer en cas de connection instable,$N❌ désactiver en revanche sur une connection lente va probablement être mieux\">full",
		"mt_fau": "sur téléphone, empêche la musique de s'arrêter de jouer si la prochaine n'est pas pré-chargée assez rapidement (peut rendre l'affichage des tags buggé)\">☕️",
		"mt_waves": "barre de progression en spectrograme:$Nmontrer l'amplitude audio dans la miniature\">~s",
		"mt_npclip": "montrer les boutons pour copier le morceau en cours de lecture\">/np",
		"mt_m3u_c": "montrer les boutons pour copier les$morceaux sélectionnées en tant qu'entrées de playlist m3u8\">📻",
		"mt_octl": "intégration os (touches de raccourci multimédia / osd)\">os-ctl",
		"mt_oseek": "permettre la recherche via l'intégration os$N$Nremarque : sur certains appareils (iPhones),$Ncela remplace le bouton de la chanson suivante\">seek",
		"mt_oscv": "montrer la couverture de l'album dans l'osd\">art",
		"mt_follow": "garder la piste en cours défilée dans la vue\">🎯",
		"mt_compact": "contrôles compacts\">⟎",
		"mt_uncache": "effacer le cache &nbsp;(essayez ceci si votre navigateur a mis en cache$Nun copie défectueuse d'une chanson, ce qui empêche sa lecture)\">uncache",
		"mt_mloop": "lire en boucle le dossier ouvert\">🔁 loop",
		"mt_mnext": "charger le dossier suivant et continuer\">📂 next",
		"mt_mstop": "arrêter la lecture\">⏸ stop",
		"mt_cflac": "convertir flac / wav en {0}\">flac",
		"mt_caac": "convertir aac / m4a en {0}\">aac",
		"mt_coth": "convertir tout les autres (pas mp3) en {0}\">oth",
		"mt_c2opus": "meilleur choix pour PC fixe, PC portable, android\">opus",
		"mt_c2owa": "opus-weba, pour iOS 17.5 et supérieur\">owa",
		"mt_c2caf": "opus-caf, pour iOS 11 à 17\">caf",
		"mt_c2mp3": "utilisez ceci sur des appareils très anciens\">mp3",
		"mt_c2flac": "meilleure qualité sonore, mais téléchargements énormes\">flac",
		"mt_c2wav": "lecture non compressée (encore plus gros)\">wav",
		"mt_c2ok": "bien, bon choix",
		"mt_c2nd": "ce n'est pas le format de sortie recommandé pour votre appareil, mais ça devrait aller",
		"mt_c2ng": "votre appareil ne semble pas prendre en charge ce format de sortie, mais essayons quand même",
		"mt_xowa": "il y a des bugs dans iOS qui empeche d'avoir une lecture en ariere plan en utilisant ce format; utilisez caf ou mp3 à la place",
		"mt_tint": "niveau d’arrière-plan (0–100) de la barre de progression$Npour rendre la mise en mémoire tampon moins gênante",
		"mt_eq": "active l'égaliseur et le contrôle de gain;$N$Nboost &lt;code&gt;0&lt;/code&gt; = volume standard 100% (non modifié)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = stéréo standard (non modifié)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% de crossfeed gauche-droite$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = suppression vocale :^)$N$Nl'activation de l'égaliseur rend les albums gapless entièrement gapless, alors laissez-le activé avec toutes les valeurs à zéro (sauf largeur = 1) si vous vous en souciez",
		"mt_drc": "active le compresseur de plage dynamique (aplanisseur de volume / brickwaller); activera également l'EQ pour équilibrer les choses, donc définissez tous les champs EQ sauf 'width' sur 0 si vous ne le voulez pas$N$Ndiminue le volume de l'audio au-dessus de THRESHOLD dB; pour chaque RATIO dB au-delà de THRESHOLD, il y a 1 dB de sortie, donc des valeurs par défaut de tresh -24 et ratio 12 signifient qu'il ne devrait jamais être plus fort que -22 dB et qu'il est sûr d'augmenter le boost de l'égaliseur à 0.8, ou même 1.8 avec ATK 0 et un énorme RLS comme 90 (ne fonctionne que dans firefox; RLS est max 1 dans les autres navigateurs)$N$N(voir wikipedia, ils expliquent cela beaucoup mieux)",

		"mb_play": "lecture",
		"mm_hashplay": "lire ce fichier audio ?",
		"mm_m3u": "appuyez sur <code>Entrée/OK</code> pour lire\nappuyez sur <code>Échap/Annuler</code> pour modifier",
		"mp_breq": "nécessite firefox 82+ ou chrome 73+ ou iOS 15+",
		"mm_bload": "chargement en cours…",
		"mm_bconv": "conversion en {0}, veuillez patienter…",
		"mm_opusen": "votre navigateur ne peut pas lire les fichiers aac / m4a ;\nle transcodage en opus est maintenant activé",
		"mm_playerr": "échec de la lecture : ",
		"mm_eabrt": "La tentative de lecture a été annulée",
		"mm_enet": "Votre connexion internet est instable ou inexistante",
		"mm_edec": "Ce fichier est supposément corrompu??",
		"mm_esupp": "Votre navigateur ne comprend pas ce format audio",
		"mm_eunk": "Erreur inconnue",
		"mm_e404": "Impossible de lire l'audio ; erreur 404 : fichier introuvable.",
		"mm_e403": "Impossible de lire l'audio ; erreur 403 : accès refusé.\n\nEssayez d'appuyer sur F5 pour recharger, peut-être que vous avez été déconnecté",
		"mm_e500": "Impossible de lire l'audio ; erreur 500 : vérifiez les journaux du serveur.",
		"mm_e5xx": "Impossible de lire l'audio ; erreur serveur ",
		"mm_nof": "Pas d'autres fichiers audio trouvés par ici",
		"mm_prescan": "En recherche d'une autre musique à lire…",
		"mm_scank": "Prochaine musique trouvée :",
		"mm_uncache": "cache vidé ; toutes les chansons seront retéléchargées lors de la prochaine lecture",
		"mm_hnf": "cette chanson n'existe plus",

		"im_hnf": "cette image n'existe plus",

		"f_empty": 'ce dossier est vide',
		"f_chide": 'ceci va cacher les colonnes «{0}»\n\ntu peut les réafficher dans les options',
		"f_bigtxt": "ce fichier fait {0} MiB -- tu veut vraiment le voir en tant que texte ?",
		"f_bigtxt2": "voir seulement la fin du fichier à la place ? ceci activera aussi le suivi en temps réel, affichant les nouvelles lignes de texte au fur et à mesure",
		"fbd_more": '<div id="blazy">showing <code>{0}</code> of <code>{1}</code> files; <a href="#" id="bd_more">show {2}</a> or <a href="#" id="bd_all">show all</a></div>',
		"fbd_all": '<div id="blazy">showing <code>{0}</code> of <code>{1}</code> files; <a href="#" id="bd_all">show all</a></div>',
		"f_anota": "seulement {0} des {1} elements sont selectioné;\npour selectioner le dossier entier, fait défiler jusqu'au fond",

		"f_dls": 'le lien de fichier dans le répertoire actuel\nà été changé en lien de téléchargement',

		"f_partial": "Pour télécharger de façon sécurisée un fichier qui est entrain de se faire téléverser, cliquez sur le fichier qui a le même nom, mais sans l'extension de fichier <code>.PARTIAL</code>. Choisissez ANNULER ou appuiez sur la touche Échap pour faire cela.\n\nAppuyer sur OK / Entrée ignorera cet avertissement et continuera à télécharger le fichier temporaire <code>.PARTIAL</code> à la place, ce qui donnera presque certainement des données corrompues.",

		"ft_paste": "coller {0} éléments$NHotkey: ctrl-V",
		"fr_eperm": 'impossible de renommer:\n vous n\'avez pas la permission “move” dans ce dossier',
		"fd_eperm": 'impossible de supprimer:\nvous n\'avez pas la permission “delete” dans ce dossier',
		"fc_eperm": 'impossible de couper:\nvous n\'avez pas la permission “move” dans ce dossier',
		"fp_eperm": 'impossible de coller:\nvous n\'avez pas la permission “write” dans ce dossier',
		"fr_emore": "sélectionnez au moins un élément à renommer",
		"fd_emore": "sélectionnez au moins un élément à supprimer",
		"fc_emore": "sélectionnez au moins un élément à couper",
		"fcp_emore": "sélectionnez au moins un élément à copier dans le presse-papiers",

		"fs_sc": "partager le dossier dans lequel vous vous trouvez",
		"fs_ss": "partager les fichiers sélectionnés",
		"fs_just1d": "vous ne pouvez pas sélectionner plus d'un dossier,\nou mélanger des fichiers et des dossiers dans une seule sélection",
		"fs_abrt": "❌ abandonner",
		"fs_rand": "🎲 nom.aleatoire",
		"fs_go": "✅ créer partage",
		"fs_name": "nom",
		"fs_src": "source",
		"fs_pwd": "mdp",
		"fs_exp": "expiration",
		"fs_tmin": "min",
		"fs_thrs": "heures",
		"fs_tdays": "jours",
		"fs_never": "éternel",
		"fs_pname": "nom de lien optionnel ; sera aléatoire si vide",
		"fs_tsrc": "le fichier ou le dossier à partager",
		"fs_ppwd": "mot de passe optionnel",
		"fs_w8": "création du partage…",
		"fs_ok": "appuyez sur <code>Entrée/OK</code> pour le Presse-papiers\nappuyez sur <code>Échap/Annuler</code> pour fermer",

		"frt_dec": "peut potentiellement réparer certaines instances de noms de fichiers cassés\">url-decode",
		"frt_rst": "réinitialiser les noms de fichiers modifiés à leurs originaux\">↺ reset",
		"frt_abrt": "abandonner et fermer cette fenêtre\">❌ cancel",
		"frb_apply": "APPLIQUER RENOMMER",
		"fr_adv": "renommage par lot / métadonnées / motif\">advanced",
		"fr_case": "regex sensible à la casse\">case",
		"fr_win": "noms windows-safe; remplacer <code>&lt;&gt;:&quot;\\|?*</code> par des caractères japonais en pleine largeur\">win",
		"fr_slash": "remplacer <code>/</code> par un caractère qui ne provoque pas la création de nouveaux dossiers\">no /",
		"fr_re": "modèle de recherche regex à appliquer aux noms de fichiers originaux ; les groupes capturés peuvent être référencés dans le champ de format ci-dessous comme &lt;code&gt;(1)&lt;/code&gt; et &lt;code&gt;(2)&lt;/code&gt; et ainsi de suite",
		"fr_fmt": "inspiré par foobar2000 : $N&lt;code&gt;(title)&lt;/code&gt; est remplacé par le titre de la chanson, $N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; saute [cette] partie si l'artiste est vide, $N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; remplit le numéro de piste à 2 chiffres",
		"fr_pdel": "supprimer",
		"fr_pnew": "enregistrer sous",
		"fr_pname": "donnez un nom pour le nouveau preset",
		"fr_aborted": "abandonné",
		"fr_lold": "ancien nom",
		"fr_lnew": "nouveau nom",
		"fr_tags": "tags pour les fichier selectioné (lecture-seule, juste pour référence):",
		"fr_busy": "renomage de {0} items…\n\n{1}",
		"fr_efail": "renomage a échoué:\n",
		"fr_nchg": "{0} des nouveaux noms ont été modifiés en raison de <code>win</code> et/ou <code>no /</code>\n\nOK pour continuer avec ces nouveaux noms modifiés ?",

		"fd_ok": "suppression réussie",
		"fd_err": "impossible de supprimer:\n",
		"fd_none": "rien n'a été supprimé ; peut-être bloqué par la configuration du serveur (xbd) ?",
		"fd_busy": "suppression de {0} éléments…\n\n{1}",
		"fd_warn1": "SUPPRIMER ces {0} éléments ?",
		"fd_warn2": "<b>Dernière chance !</b> Impossible de revenir en arrière. Supprimer ?",

		"fc_ok": "couper {0} éléments",
		"fc_warn": 'couper {0} éléments\n\nmais : seul <b>cet</b> onglets peut les coller\n(puisque la sélection est si absolument massive)',

		"fcc_ok": "copié {0} éléments dans le presse-papiers",
		"fcc_warn": 'copié {0} éléments dans le presse-papiers\n\nmais : seul <b>cet</b> onglet peut les coller\n(puisque la sélection est si absolument massive)',

		"fp_apply": "utiliser ces noms",
		"fp_ecut": "en premier, coupez ou copiez quelques fichiers / dossiers à coller / déplacer\n\nnote: vous pouvez couper / coller a travers different onglets",
		"fp_ename": "{0} éléments ne peuvent pas être déplacés ici parceque leurs noms sont déjà pris. Donnez leurs un nouveau nom ci-dessous pour continuer, ou laissez les vides pour les sauter:",
		"fcp_ename": "{0} éléments ne peuvent pas être copiés ici parce que les noms sont déjà pris. Donnez-leur un nouveau nom ci-dessous pour continuer, ou laissez-les vides pour les sauter :",
		"fp_emore": "il reste encore des collisions de noms de fichiers à corriger",
		"fp_ok": "déplacement OK",
		"fcp_ok": "copie OK",
		"fp_busy": "déplacement de {0} éléments…\n\n{1}",
		"fcp_busy": "copie de {0} éléments…\n\n{1}",
		"fp_abrt": "abandon en cours...", //m
		"fp_err": "deplacement échoué:\n",
		"fcp_err": "copie échouée:\n",
		"fp_confirm": "déplacer ces {0} éléments ici ?",
		"fcp_confirm": "copier ces {0} éléments ici ?",
		"fp_etab": 'lecture du presse-papier venant d\'un autre onglet échoué',
		"fp_name": "téléversement d'un fichier de votre apareil. Donnez lui un nom:",
		"fp_both_m": '<h6>choisisez ce qu\'il faut coller</h6><code>Entrer</code> = Déplacer {0} fichiers de «{1}»\n<code>ESC</code> = Téléverser {2} fichiers de votre appareil',
		"fcp_both_m": '<h6>choisissez ce qu\'il faut coller</h6><code>Entrer</code> = Copier {0} fichiers de «{1}»\n<code>ESC</code> = Téléverser {2} fichiers de votre appareil',
		"fp_both_b": '<a href="#" id="modal-ok">Déplacer</a><a href="#" id="modal-ng">Téléverser</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Copier</a><a href="#" id="modal-ng">Téléverser</a>',

		"mk_noname": "entrez un nom dans le champ de texte à gauche avant de faire ça :p",

		"tv_load": "Chargement du document texte:\n\n{0}\n\n{1}% ({2} de {3} MiB chargés)",
		"tv_xe1": "impossible de charger le fichier texte:\n\nerreur",
		"tv_xe2": "404, fichier introuvable",
		"tv_lst": "liste des fichiers texte dans",
		"tvt_close": "retour a la vue de dossier$NHotkey: M (ou Échap)\">❌ fermer",
		"tvt_dl": "télécharger ce fichier$NHotkey: Y\">💾 télécharger",
		"tvt_prev": "montrer le document précédent$NHotkey: i\">⬆ précédent",
		"tvt_next": "montrer le document suivant$NHotkey: K\">⬇ suivant",
		"tvt_sel": "sélectionner le fichier &nbsp; ( pour couper / copier / supprimer / … )$NHotkey: S\">sel",
		"tvt_edit": "ouvrir le fichier dans l'éditeur de texte$NHotkey: E\">✏️ modifier",
		"tvt_tail": "surveiller le fichier pour les changements; montrer les nouvelles lignes en temps réel\">📡 suivre",
		"tvt_wrap": "retour à la ligne\">↵",
		"tvt_atail": "ancrer le défilement au fond de la page\">⚓",
		"tvt_ctail": "décoder les couleurs du terminal (ansi escape codes)\">🌈",
		"tvt_ntail": "limite de défilement en arrière (combien d'octets de texte à garder chargé)",

		"m3u_add1": "musique ajoutée à la playlist m3u",
		"m3u_addn": "{0} musiques ajoutées à la playlist m3u",
		"m3u_clip": "la playlist m3u est maintenant copiée dans le presse-papier\n\nvous devriez créer un nouveau fichier texte nommé par exemple playlist.m3u et coller la playlist dans ce fichier ; cela la rendra lisible en tant que playlist",

		"gt_vau": "ne pas voir les vidéos, juste jouer l'audio\">🎧",
		"gt_msel": "activer la séléction de fichiers ; ctrl-clic sur un fichier pour override écraser$N$N<em>quand actif : double-cliquer sur un fichier / dossier pour l'ouvrir</em>$N$NHotkey: S\">multiséléction",
		"gt_crop": "rogner les miniatures au centre\"&gt;rogner",
		"gt_3x": "miniatures haute résolution\">3x",
		"gt_zoom": "zoomer",
		"gt_chop": "rogner",
		"gt_sort": "trier par",
		"gt_name": "nom",
		"gt_sz": "taille",
		"gt_ts": "date",
		"gt_ext": "type",
		"gt_c1": "tronquer les noms de fichiers (montrer moins)",
		"gt_c2": "tronquer les noms de fichiers (montrer plus)",

		"sm_w8": "recherche…",
		"sm_prev": "les résultats de recherche ci-dessous proviennent d'une requête précédente:\n  ",
		"sl_close": "fermer les résultats de recherche",
		"sl_hits": "affichage de {0} résultats",
		"sl_moar": "chercher plus",

		"s_sz": "taille",
		"s_dt": "date",
		"s_rd": "chemin",
		"s_fn": "nom",
		"s_ta": "tags",
		"s_ua": "up@",
		"s_ad": "adv.",
		"s_s1": "minimum MiB",
		"s_s2": "maximum MiB",
		"s_d1": "min. iso8601",
		"s_d2": "max. iso8601",
		"s_u1": "téléverser après",
		"s_u2": "et/ou avant",
		"s_r1": "le chemin contient &nbsp; (séparé par des espaces)",
		"s_f1": "le nom contient &nbsp; (négation avec -nope)",
		"s_t1": "les tags contiennent &nbsp; (^=début, fin=$)",
		"s_a1": "propriétés de métadonnées spécifiques",

		"md_eshow": "impossible d'afficher le rendu ",
		"md_off": "[📜<em>readme</em>] disabled in [⚙️] -- document caché",

		"badreply": "Échec de l'analyse de la réponse du serveur",

		"xhr403": "403: Accès refusé\n\nessayez d'appuyer sur F5, peut-être que vous avez été déconnecté",
		"xhr0": "inconnu (vous avez probablement perdu la connexion au serveur, ou le serveur est hors ligne)",
		"cf_ok": "désolé pour cela -- la protection DD" + wah + "oS a été déclenché\n\nles choses devraient reprendre dans environ 30 secondes\n\nsi rien ne se passe, appuyez sur F5 pour recharger la page",
		"tl_xe1": "impossible de lister les sous-dossiers:\n\nerreur ",
		"tl_xe2": "404: Dossier introuvable",
		"fl_xe1": "impossible de lister les fichiers dans le dossier:\n\nerreur ",
		"fl_xe2": "404: Dossier introuvable",
		"fd_xe1": "impossible de créer le sous-dossier:\n\nerreur ",
		"fd_xe2": "404: Dossier parent introuvable",
		"fsm_xe1": "impossible d'envoyer le message:\n\nerreur ",
		"fsm_xe2": "404: Dossier parent introuvable",
		"fu_xe1": "échec du chargement de la liste des unpost du serveur:\n\nerreur ",
		"fu_xe2": "404: Fichier introuvable??",

		"fz_tar": "fichier gnu-tar non compressé (linux / mac)",
		"fz_pax": "tar au format pax non compressé (plus lent)",
		"fz_targz": "gnu-tar avec compression gzip niveau 3$N$Ncela est généralement très lent, donc$Nutilisez plutôt tar non compressé",
		"fz_tarxz": "gnu-tar avec compression xz niveau 1$N$Ncela est généralement très lent, donc$Nutilisez plutôt tar non compressé",
		"fz_zip8": "zip avec noms de fichiers utf8 (peut être instable sur windows 7 et versions antérieures)",
		"fz_zipd": "zip avec noms de fichiers cp437 traditionnels, pour les très anciens logiciels",
		"fz_zipc": "cp437 avec crc32 calculé tôt,$Nfor MS-DOS PKZIP v2.04g (octobre 1993)$N(prend plus de temps à charger avant que le téléchargement ne commence)",

		"un_m1": "vous pouvez supprimer vos téléchargements récents (ou annuler ceux en cours) ci-dessous",
		"un_upd": "rafraîchir",
		"un_m4": "ou partager les fichiers visibles ci-dessous:",
		"un_ulist": "montrer",
		"un_ucopy": "copier",
		"un_flt": "filtre optionnel:&nbsp; l'URL doit contenir",
		"un_fclr": "effacer le filtre",
		"un_derr": 'échec de l\'unpost-delete:\n',
		"un_f5": 'quelque chose a cassé, veuillez essayer de rafraîchir ou d\'appuyer sur F5',
		"un_uf5": "désolé mais vous devez rafraîchir la page (par exemple en appuyant sur F5 ou CTRL-R) avant que ce téléchargement puisse être annulé",
		"un_nou": '<b>warning:</b> serveur trop occupé pour afficher les téléversements non finis; cliquez sur le lien "rafraîchir" dans un instant',
		"un_noc": '<b>warning:</b> unpost des fichiers entièrement téléchargés n\'est pas activé/permis dans la configuration du serveur',
		"un_max": "affichage des 2000 premiers fichiers (utilisez le filtre)",
		"un_avail": "{0} téléchargements récents peuvent être supprimés<br />{1} ceux en cours peuvent être annulés",
		"un_m2": "triés par date de téléchargement; les plus récents en premier:",
		"un_no1": "sike! aucun téléchargement n'est suffisamment récent",
		"un_no2": "sike! aucun téléchargement correspondant à ce filtre n'est suffisamment récent",
		"un_next": "supprimer les {0} fichiers suivants ci-dessous",
		"un_abrt": "abandonner",
		"un_del": "supprimer",
		"un_m3": "chargement de vos téléchargements récents…",
		"un_busy": "suppression de {0} fichiers…",
		"un_clip": "{0} liens copiés dans le presse-papiers",

		"u_https1": "vous devriez",
		"u_https2": "passer à https",
		"u_https3": "pour de meilleure performances",
		"u_ancient": 'votre navigateur est impressionnamment ancien -- vous devriez peut-être <a href="#" onclick="goto(\'bup\')">utiliser bup à la place</a>',
		"u_nowork": "nécessite firefox 53+ ou chrome 57+ ou iOS 11+",
		"tail_2old": "nécessite firefox 105+ ou chrome 71+ ou iOS 14.5+",
		"u_nodrop": 'votre navigateur est trop ancien pour le téléversement par glisser-déposer',
		"u_notdir": "ce n'est pas un dossier!\n\nvotre navigateur est trop ancien,\nveuillez essayer le glisser-déposer à la place",
		"u_uri": "pour glisser-déposer des images depuis d'autres fenêtres de navigateur,\nveuillez les déposer sur le gros bouton de téléversement",
		"u_enpot": 'passer à <a href="#">l\'interface utilisateur potato</a> (peut améliorer la vitesse de téléversement)',
		"u_depot": 'passer à <a href="#">l\'interface utilisateur fancy</a> (peut réduire la vitesse de téléversement)',
		"u_gotpot": 'passage à l\'interface utilisateur potato pour une vitesse de téléversement améliorée,\n\nn\'hésitez pas à revenir en arrière si ça ne vous plaît pas !',
		"u_pott": "<p>fichiers: &nbsp; <b>{0}</b> fini, &nbsp; <b>{1}</b> échoué, &nbsp; <b>{2}</b> en cours, &nbsp; <b>{3}</b> en attente</p>",
		"u_ever": "ceci est le téléverseur de base ; up2k nécessite au moins chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'ceci est le téléverseur de base; <a href="#" id="u2yea">up2k</a> est meilleur',
		"u_uput": 'optimiser pour la vitesse (ignorer la somme de contrôle)',
		"u_ewrite": 'vous n\'avez pas accès en écriture à ce dossier',
		"u_eread": 'vous n\'avez pas accès en lecture à ce dossier',
		"u_enoi": 'la recherche de fichiers n\'est pas activée dans la configuration du serveur',
		"u_enoow": "l'écrasage ne fonctionnera pas ici; besoin de permissions de suppression",
		"u_badf": 'Ces {0} fichiers (sur {1} au total) ont été ignorés, probablement en raison de permissions système de fichiers:\n\n',
		"u_blankf": 'Ces {0} fichiers (sur {1} au total) sont vides; les téléverser quand même ?\n\n',
		"u_applef": 'Ces {0} fichiers (sur {1} au total) sont probablement indésirables;\nAppuyez sur <code>OK/Enter</code> pour IGNORER les fichiers suivants,\nAppuyez sur <code>Annuler/Échap</code> pour NE PAS exclure, et TÉLÉVERSER ceux-ci également:\n\n',
		"u_just1": '\nPeut-être que cela fonctionne mieux si vous sélectionnez juste un fichier',
		"u_ff_many": "si vous utilisez <b>Linux / MacOS / Android,</b> alors ce nombre de fichiers <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>peut</em> faire planter Firefox!</a>\nSi cela se produit, veuillez réessayer (ou utiliser Chrome).",
		"u_up_life": "Ce téléversement va être supprimé du serveur\n{0} après son achèvement",
		"u_asku": 'téléverser ces {0} fichiers vers <code>{1}</code>',
		"u_unpt": "vous pouvez défaire / supprimer ce téléversement en utilisant le 🧯 en haut à gauche",
		"u_bigtab": 'sur le point d\'afficher {0} fichiers\n\ncela peut faire planter votre navigateur, êtes-vous sûr ?',
		"u_scan": 'Analyse des fichiers…',
		"u_dirstuck": 'l\'itérateur de répertoire est bloqué en essayant d\'accéder aux {0} éléments suivants ; il sera ignoré :',
		"u_etadone": 'Terminé ({0}, {1} fichiers)',
		"u_etaprep": '(préparation au téléversement)',
		"u_hashdone": 'calcul de la somme de contrôle terminé',
		"u_hashing": 'calcul de la somme de contrôle',
		"u_hs": 'établissement d\'une liaison…',
		"u_started": "les fichiers sont maintenant en cours de téléversement ; voir [🚀]",
		"u_dupdefer": "dupliqué ; sera traité après tous les autres fichiers",
		"u_actx": "cliquez sur ce texte pour éviter la perte de<br />performance lors du passage à d'autres fenêtres/onglets",
		"u_fixed": "OK!&nbsp; Résolu 👍",
		"u_cuerr": "echec du téléversement du morceau {0} de {1};\nprobablement inoffensif, poursuite\n\nfichier : {2}",
		"u_cuerr2": "le serveur a rejeté le téléversement (morceau {0} de {1});\nréessaiera plus tard\n\nfichier : {2}\n\nerreur ",
		"u_ehstmp": "réessaiera ; voir en bas à droite",
		"u_ehsfin": "le serveur a rejeté la demande de finalisation du téléversement ; nouvelle tentative…",
		"u_ehssrch": "le serveur a rejeté la demande d'effectuer une recherche ; nouvelle tentative…",
		"u_ehsinit": "le serveur a rejeté la demande d'initier le téléversement ; nouvelle tentative…",
		"u_eneths": "erreur réseau lors de l'exécution de l'initialisation du téléversement ; nouvelle tentative…",
		"u_enethd": "erreur réseau lors du test de l'existence de la cible ; nouvelle tentative…",
		"u_cbusy": "attente que le serveur nous fasse à nouveau confiance après un problème réseau…",
		"u_ehsdf": "le serveur est à court d'espace disque !\n\nil va continuer de réessayer, au cas où quelqu'un\nlibérerait suffisamment d'espace pour continuer",
		"u_emtleak1": "il semble que votre navigateur web ait une fuite de mémoire ;\nveuillez",
		"u_emtleak2": ' <a href="{0}">passer à https (recommandé)</a> ou ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'essayez la solution suivante:\n<ul><li>appuyez sur <code>F5</code> pour rafraîchir la page</li><li>ensuite désactivez le bouton &nbsp;<code>mt</code>&nbsp; dans les &nbsp;<code>⚙️ paramètres</code></li><li>et réessayez ce téléversement</li></ul>Les téléversements seront un peu plus lents, mais tant pis.\nDésolé pour le dérangement !\n\nPS : chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">a un correctif</a> pour cela',
		"u_emtleakf": 'essayez la solution suivante:\n<ul><li>appuyez sur <code>F5</code> pour rafraîchir la page</li><li>ensuite activez <code>🥔</code> (pomme de terre) dans l\'interface de téléversement</li><li>et réessayez ce téléversement</li></ul>\nPS : firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">aura probablement un correctif</a> à un moment donné',
		"u_s404": "pas trouvé sur le serveur",
		"u_expl": "expliquer",
		"u_maxconn": "la plupart des navigateur limite ceci à 6, mais firefox vous permet de l'augmenter avec <code>connections-per-server</code> dans <code>about:config</code>",
		"u_tu": '<p class="warn">WARNING: turbo enclenché, <span>&nbsp;le client peut ne pas détecter et reprendre les téléversements incomplets ; voir l\'info-bulle du bouton turbo</span></p>',
		"u_ts": '<p class="warn">WARNING: turbo enclenché, <span>&nbsp;les résultats de recherche peuvent être incorrects ; voir l\'info-bulle du bouton turbo</span></p>',
		"u_turbo_c": "turbo est désactivé dans la configuration du serveur",
		"u_turbo_g": "désactivation de turbo car vous n'avez pas de\nprivilèges de listing de répertoires dans ce volume",
		"u_life_cfg": 'suppression automatique après <input id="lifem" p="60" /> min (ou <input id="lifeh" p="3600" /> heures)',
		"u_life_est": 'le téléversement sera supprimé <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'ce dossier impose une\ndurée de vie maximale de {0}',
		"u_unp_ok": 'unpost est autorisé pour {0}',
		"u_unp_ng": 'unpost ne sera PAS autorisé',
		"ue_ro": 'votre accès à ce dossier est en lecture seule\n\n',
		"ue_nl": 'vous n\'êtes actuellement pas connecté',
		"ue_la": 'vous êtes actuellement connecté en tant que "{0}"',
		"ue_sr": 'vous êtes actuellement en mode recherche de fichiers\n\nchangez en mode téléversement en cliquant sur la loupe 🔎 (à côté du grand bouton RECHERCHER), et essayez de téléverser à nouveau\n\ndésolé',
		"ue_ta": 'essayez de téléverser à nouveau, cela devrait fonctionner maintenant',
		"ue_ab": "ce fichier a déjà été téléversé dans un autre dossier, et ce téléversement doit être terminé avant que le fichier puisse être téléversé ailleurs.\n\nVous pouvez annuler et oublier le téléversement initial en utilisant le bouton 🧯 en haut à gauche.",
		"ur_1uo": "OK: Fichier téléversé avec succès",
		"ur_auo": "OK: Tous les {0} fichiers téléversés avec succès",
		"ur_1so": "OK: Fichier trouvé sur le serveur",
		"ur_aso": "OK: Tous les {0} fichiers trouvés sur le serveur",
		"ur_1un": "Échec du téléversement, désolé",
		"ur_aun": "Tous les {0} téléversements ont échoué, désolé",
		"ur_1sn": "Fichier NON trouvé sur le serveur",
		"ur_asn": "Les {0} fichiers n'ont PAS ÉTÉ trouvés sur le serveur",
		"ur_um": "Terminé;\n{0} téléversements OK,\n{1} téléversements échoués, désolé",
		"ur_sm": "Terminé;\n{0} fichiers trouvés sur le serveur,\n{1} fichiers NON trouvés sur le serveur",

		"lang_set": "rafraîchir pour que les changements prennent effet ?",
	},
	"grc": {
		"tt": "Ελληνικά",

		"cols": {
			"c": "κουμπιά ενεργειών",
			"dur": "διάρκεια",
			"q": "ποιότητα / bitrate",
			"Ac": "κωδικοποιητής ήχου",
			"Vc": "κωδικοποιητής βίντεο",
			"Fmt": "μορφή / container",
			"Ahash": "checksum ήχου",
			"Vhash": "checksum βίντεο",
			"Res": "ανάλυση",
			"T": "τύπος αρχείου",
			"aq": "ποιότητα ήχου / bitrate",
			"vq": "ποιότητα βίντεο / bitrate",
			"pixfmt": "subsampling / δομή εικονοστοιχείων",
			"resw": "οριζόντια ανάλυση",
			"resh": "κάθετη ανάλυση",
			"chs": "κανάλια ήχου",
			"hz": "συχνότητα δειγματοληψίας"
		},

		"hks": [
			[
				"διάφορα",
				["ESC", "κλείσιμο διαφόρων λειτουργιών"],

				"διαχειριστής αρχείων",
				["G", "εναλλαγή λίστας / πλέγματος"],
				["T", "εναλλαγή μικρογραφιών / εικονιδίων"],
				["⇧ A/D", "μέγεθος μικρογραφιών"],
				["ctrl-K", "διαγραφή επιλεγμένων"],
				["ctrl-X", "αποκοπή επιλογής στο πρόχειρο"],
				["ctrl-C", "αντιγραφή επιλογής στο πρόχειρο"],
				["ctrl-V", "επικόλληση (μετακίνηση/αντιγραφή) εδώ"],
				["Y", "λήψη επιλεγμένων"],
				["F2", "μετονομασία επιλεγμένων"],

				"λίστα αρχείων",
				["space", "εναλλαγή επιλογής αρχείου"],
				["↑/↓", "μετακίνηση δείκτη επιλογής"],
				["ctrl ↑/↓", "μετακίνηση δείκτη και προβολής"],
				["⇧ ↑/↓", "επιλογή προηγούμενου/επόμενου αρχείου"],
				["ctrl-A", "επιλογή όλων των αρχείων / φακέλων"]
			], [
				"πλοήγηση",
				["B", "εναλλαγή σε καρτέλες διαδρομών / δέντρο διαδρομών"],
				["I/K", "προηγούμενος/επόμενος φάκελος"],
				["M", "γονικός φάκελος (ή σμίκρυνση τρέχοντος)"],
				["V", "εναλλαγή φακέλων / δέντρο αρχείων κειμένου"],
				["A/D", "μέγεθος πίνακα πλοήγησης"]
			], [
				"μουσική",
				["J/L", "προηγούμενο/επόμενο τραγούδι"],
				["U/O", "μετάβαση 10δευτ πίσω/μπροστά"],
				["0..9", "μετάβαση στο 0%..90%"],
				["P", "αναπαραγωγή/παύση (ξεκινάει κιόλας)"],
				["S", "επιλογή αναπαραγόμενου τραγουδιού"],
				["Y", "λήψη τραγουδιού"]
			], [
				"εικόνες",
				["J/L, ←/→", "προηγούμενη/επόμενη εικόνα"],
				["Home/End", "πρώτη/τελευταία εικόνα"],
				["F", "πλήρης οθόνη"],
				["R", "περιστροφή δεξιόστροφα"],
				["⇧ R", "περιστροφή αριστερόστροφα"],
				["S", "επιλογή εικόνας"],
				["Y", "λήψη εικόνας"]
			], [
				"βίντεο",
				["U/O", "μετάβαση 10δευτ πίσω/μπροστά"],
				["P/K/Space", "αναπαραγωγή/παύση"],
				["C", "συνέχεια στο επόμενο"],
				["V", "επανάληψη"],
				["M", "σίγαση"],
				["[ και ]", "ορισμός διαστήματος επανάληψης"]
			], [
				"αρχεία κειμένου",
				["I/K", "προηγούμενο/επόμενο αρχείο"],
				["M", "κλείσιμο αρχείου"],
				["E", "επεξεργασία αρχείου"],
				["S", "επιλογή αρχείου (για αποκοπή/αντιγραφή/μετονομασία)"]
			]
		],

		"m_ok": "Εντάξει",
		"m_ng": "Άκυρο",

		"enable": "Ενεργοποίηση",
		"danger": "ΚΙΝΔΥΝΟΣ",
		"clipped": "αντιγράφηκε στο πρόχειρο",

		"ht_s1": "δευτερόλεπτο",
		"ht_s2": "δευτερόλεπτα",
		"ht_m1": "λεπτό",
		"ht_m2": "λεπτά",
		"ht_h1": "ώρα",
		"ht_h2": "ώρες",
		"ht_d1": "μέρα",
		"ht_d2": "μέρες",
		"ht_and": " και ",

		"goh": "πίνακας ελέγχου",
		"gop": 'προηγούμενος φάκελος στο ίδιο επίπεδο">προηγούμενο',
		"gou": 'γονικός φάκελος">πάνω',
		"gon": 'επόμενος φάκελος">επόμενο',
		"logout": "Αποσύνδεση ",
		"login": "Σύνδεση", //m
		"access": " πρόσβαση",
		"ot_close": "κλείσιμο υπομενού",
		"ot_search": "αναζήτηση αρχείων με βάση χαρακτηριστικά, διαδρομή / όνομα, μουσικά tags ή οποιονδήποτε συνδυασμό$N$N&lt;code&gt;foo bar&lt;/code&gt; = πρέπει να περιέχει και τα «foo» και «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = πρέπει να περιέχει το «foo» αλλά όχι το «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = να ξεκινά με «yana» και να είναι αρχείο «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = να περιέχει ακριβώς «try unite»$N$Nη μορφή ημερομηνίας είναι iso-8601, όπως$N&lt;code&gt;2009-12-31&lt;/code&gt; ή &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: διαγραφή πρόσφατων μεταφορτώσεων ή ακύρωση ανολοκλήρωτων",
		"ot_bup": "bup: βασικός uploader, υποστηρίζει μέχρι και netscape 4.0",
		"ot_mkdir": "mkdir: δημιουργία νέου φακέλου",
		"ot_md": "new-md: δημιουργία νέου markdown εγγράφου",
		"ot_msg": "msg: αποστολή μηνύματος στο server log",
		"ot_mp": "επιλογές media player",
		"ot_cfg": "επιλογές ρυθμίσεων",
		"ot_u2i": 'up2k: ανέβασε αρχεία (αν έχεις δικαίωμα εγγραφής) ή ενεργοποίησε τη λειτουργία αναζήτησης για να δεις αν υπάρχουν ήδη στο server$N$Nοι μεταφορτώσεις συνεχίζονται αν διακοπούν, είναι πολυνηματικές και διατηρούν τις χρονοσφραγίδες, αλλά καταναλώνουν περισσότερο CPU από τον [🎈]&nbsp; (βασικός uploader)<br /><br />κατά τη διάρκεια της μεταφόρτωσης, αυτό το εικονίδιο δείχνει την πρόοδό της!',
		"ot_u2w": 'up2k: ανέβασε αρχεία με υποστήριξη συνέχισης (κλείσε τον browser και ρίξε τα ίδια αρχεία ξανά μετά)$N$Nπολυνηματικό, διατηρεί τις χρονοσφραγίδες, αλλά καταναλώνει περισσότερο CPU από τον [🎈]&nbsp; (βασικός uploader)<br /><br />κατά τη διάρκεια της μεταφόρτωσης, αυτό το εικονίδιο δείχνει την πρόοδό της!',
		"ot_noie": 'Χρησιμοποίησε Chrome / Firefox / Edge',

		"ab_mkdir": "δημιουργία φακέλου",
		"ab_mkdoc": "νέο markdown έγγραφο",
		"ab_msg": "στείλε μήνυμα στο server log",

		"ay_path": "πήγαινε σε φακέλους",
		"ay_files": "πήγαινε σε αρχεία",

		"wt_ren": "μετονομασία επιλεγμένων$NΣυντόμευση: F2",
		"wt_del": "διαγραφή επιλεγμένων$NΣυντόμευση: ctrl-K",
		"wt_cut": "αποκοπή επιλεγμένων &lt;small&gt;(και επικόλληση αλλού)&lt;/small&gt;$NΣυντόμευση: ctrl-X",
		"wt_cpy": "αντιγραφή επιλεγμένων στο πρόχειρο$N(για επικόλληση αλλού)$NΣυντόμευση: ctrl-C",
		"wt_pst": "επικόλληση αποκομμένων / αντεγραμμένων$NΣυντόμευση: ctrl-V",
		"wt_selall": "επιλογή όλων$NΣυντόμευση: ctrl-A (με το αρχείο επιλεγμένο)",
		"wt_selinv": "αντιστροφή επιλογής",
		"wt_zip1": "κατέβασμα φακέλου ως συμπιεσμένο αρχείο",
		"wt_selzip": "κατέβασμα επιλογής ως συμπιεσμένο αρχείο",
		"wt_seldl": "κατέβασμα επιλογής ως μεμονωμένα αρχεία$NΣυντόμευση: Y",
		"wt_npirc": "αντιγραφή πληροφοριών τραγουδιού σε μορφή irc",
		"wt_nptxt": "αντιγραφή πληροφοριών τραγουδιού ως κείμενο",
		"wt_m3ua": "προσθήκη σε m3u λίστα αναπαραγωγής (μετά πάτησε <code>📻αντιγραφή</code>)",
		"wt_m3uc": "αντιγραφή m3u λίστας αναπαραγωγής στο πρόχειρο",
		"wt_grid": "εναλλαγή πλέγματος / λίστας$NΣυντόμευση: G",
		"wt_prev": "προηγούμενο κομμάτι$NΣυντόμευση: J",
		"wt_play": "αναπαραγωγή / παύση$NΣυντόμευση: P",
		"wt_next": "επόμενο κομμάτι$NΣυντόμευση: L",

		"ul_par": "παράλληλες μεταφορτώσεις:",
		"ut_rand": "τυχαιοποίηση ονομάτων αρχείων",
		"ut_u2ts": "αντιγραφή της τελευταίας τροποποιημένης χρονοσφραγίδας αλλαγής$Nαπό το σύστημά σου στον server\">📅",
		"ut_ow": "αντικατάσταση σε ήδη υπάρχοντα αρχεία του server?$N🛡️: ποτέ (θα δημιουργηθεί νέο όνομα)$N🕒: αν το αρχείο του server είναι παλαιότερο$N♻️: πάντα να αντικαθίστανται αν διαφέρουν",
		"ut_mt": "συνέχιση υπολογισμού hash για άλλα αρχεία κατά τη μεταφόρτωση$N$Nαπενεργοποίησέ το αν η CPU ή ο δίσκος σου ζορίζονται",
		"ut_ask": 'επιβεβαίωση πριν ξεκινήσει η μεταφόρτωση">💭',
		"ut_pot": "βελτίωση ταχύτητας μεταφόρτωσης σε αργές συσκευές$Nμε απλοποίηση του UI",
		"ut_srch": "μην ανεβάζεις, έλεγξε αν τα αρχεία$Nυπάρχουν ήδη στον server (ψάχνει σε όλους τους φακέλους που έχεις πρόσβαση)",
		"ut_par": "κάνε παύση στις μεταφορτώσεις βάζοντάς το 0$N$Nαύξησε το αν έχεις αργή/μεγάλη καθυστέρηση σύνδεσης$N$Nκράτα το 1 σε LAN ή αν ο server έχει αργό δίσκο",
		"ul_btn": "ρίξε αρχεία / φακέλους<br>εδώ (ή κάνε κλικ σε μένα)",
		"ul_btnu": "Μ Ε Τ Α Φ Ο Ρ Τ Ω Σ Η",
		"ul_btns": "Α Ν Α Ζ Η Τ Η Σ Η",

		"ul_hash": "υπολογισμός hash",
		"ul_send": "αποστολή",
		"ul_done": "ολοκληρώθηκε",
		"ul_idle1": "καμία μεταφόρτωση στην ουρά για την ώρα",
		"ut_etah": "μέση ταχύτητα &lt;em&gt;υπολογισμού hash&lt;/em&gt; και εκτίμηση χρόνου μέχρι την ολοκλήρωση",
		"ut_etau": "μέση ταχύτητα &lt;em&gt;μεταφόρτωσης&lt;/em&gt; και εκτίμηση χρόνου μέχρι την ολοκλήρωση",
		"ut_etat": "μέση &lt;em&gt;συνολική&lt;/em&gt; ταχύτητα και εκτίμηση χρόνου μέχρι την ολοκλήρωση",

		"uct_ok": "ολοκληρώθηκε επιτυχώς",
		"uct_ng": "no-good: απέτυχε / απορρίφθηκε / δεν βρέθηκε",
		"uct_done": "ολοκληρωμένα και αποτυχημένα",
		"uct_bz": "κάνει hash ή μεταφορτώνει",
		"uct_q": "σε αναμονή, εκκρεμεί",

		"utl_name": "όνομα αρχείου",
		"utl_ulist": "λίστα",
		"utl_ucopy": "αντιγραφή",
		"utl_links": "σύνδεσμοι",
		"utl_stat": "κατάσταση",
		"utl_prog": "πρόοδος",

		// keep short:
		"utl_404": "404",
		"utl_err": "ΣΦΑΛΜΑ",
		"utl_oserr": "ΣΦ-ΛΕ",
		"utl_found": "βρέθηκε",
		"utl_defer": "αναβολή",
		"utl_yolo": "YOLO",
		"utl_done": "έγινε",

		"ul_flagblk": "τα αρχεία προστέθηκαν στην ουρά</b><br>αλλά υπάρχει άλλη ενεργή μεταφόρτωση σε άλλη καρτέλα,<br>οπότε περίμενε να τελειώσει αυτό πρώτα",
		"ul_btnlk": "ο διακομιστής έχει κλειδώσει αυτήν την επιλογή σε αυτήν την κατάσταση",

		"udt_up": "Μεταφόρτωση",
		"udt_srch": "Αναζήτηση",
		"udt_drop": "ρίξ' το εδώ",

		"u_nav_m": '<h6>οκ, τι έχουμε εδώ;</h6><code>Enter</code> = Αρχεία (ένα ή περισσότερα)\n<code>ESC</code> = Ένας φάκελος (μαζί με υποφακέλους)',
		"u_nav_b": '<a href="#" id="modal-ok">Αρχεία</a><a href="#" id="modal-ng">Ένας φάκελος</a>',

		"cl_opts": "διακόπτες",
		"cl_themes": "θέμα",
		"cl_langs": "γλώσσα",
		"cl_ziptype": "λήψη φακέλου",
		"cl_uopts": "διακόπτες μεταφόρτωσης",
		"cl_favico": "favicon",
		"cl_bigdir": "μεγάλοι φάκελοι",
		"cl_hsort": "#ταξινόμηση",
		"cl_keytype": "σημείωση πλήκτρων",
		"cl_hiddenc": "κρυφές στήλες",
		"cl_hidec": "κρύψε",
		"cl_reset": "επανεκκίνηση",
		"cl_hpick": "πάτησε στις κεφαλίδες στηλών για να τις κρύψεις στον πίνακα παρακάτω",
		"cl_hcancel": "η απόκρυψη στηλών ακυρώθηκε",

		"ct_grid": '田 το πλέγμα',
		"ct_ttips": '◔ ◡ ◔">ℹ️ συμβουλές εργαλείων',
		"ct_thumb": 'σε προβολή πλέγματος, εναλλαγή εικονιδίων ή μικρογραφιών$NΠλήκτρο συντόμευσης: T">🖼️ μικρογραφίες',
		"ct_csel": 'χρησιμοποίησε CTRL και SHIFT για επιλογή αρχείων σε προβολή πλέγματος">επιλογή',
		"ct_ihop": 'όταν η προβολή εικόνων κλείνει, κάνε scroll στο τελευταίο προβαλλόμενο αρχείο">g⮯',
		"ct_dots": 'εμφάνιση κρυφών αρχείων (αν το επιτρέπει ο server)">dotfiles',
		"ct_qdel": 'όταν διαγράφεις αρχεία, ζήτα επιβεβαίωση μόνο μία φορά">γρήγορη διαγραφή',
		"ct_dir1st": 'ταξινόμηση φακέλων πριν από τα αρχεία">📁 πρώτα',
		"ct_nsort": 'φυσική ταξινόμηση (για ονόματα αρχείων με αριθμούς στην αρχή)">φυσική ταξινόμηση',
		"ct_utc": 'εμφάνιση όλων των ημερομηνιών σε UTC">UTC',
		"ct_readme": 'εμφάνιση README.md στις λίστες φακέλων">📜 πληροφορίες',
		"ct_idxh": 'εμφάνιση index.html αντί για λίστα φακέλων">html',
		"ct_sbars": 'εμφάνιση μπαρών κύλισης">⟊',

		"cut_umod": "αν το αρχείο υπάρχει ήδη στον server, ενημέρωσέ το με την τελευταία χρονοσφραγίδα τροποποίησης για να ταιριάζει με το τοπικό αρχείο (απαιτεί δικαιώματα εγγραφής+διαγραφής)\">re📅",

		"cut_turbo": "το κουμπί yolo, πιθανόν να ΜΗΝ ΘΕΛΕΙΣ να το ενεργοποιήσεις:$N$Nχρησιμοποίησέ το αν μεταφορτώνεις πολλά αρχεία και χρειάστηκε να ξαναρχίσεις, και θες να συνεχίσεις τη μεταφότρωση όσο το δυνατόν πιο γρήγορα$N$Nαντικαθιστά τον έλεγχο hash με απλό <em>&quot;έχει το ίδιο μέγεθος αρχείου στον server?&quot;</em> οπότε αν το περιεχόμενο είναι διαφορετικό, ΔΕΝ θα ανέβει$N$Nπρέπει να το κλείσεις όταν τελειώσει η μεταφόρτωση και μετά να &quot;μεταφορτώσεις&quot; πάλι τα ίδια αρχεία για να τα επιβεβαιώσει το τοπικό σου πρόγραμμα\">turbo",

		"cut_datechk": "δεν επηρεάζει τίποτα εκτός αν το turbo είναι ενεργοποιημένο$N$Nμειώνει λίγο τον παράγοντα yolo; ελέγχει αν οι χρονοσφραγίδες στο διακομιστή ταιριάζουν με τα δικά σου$N$Nπιάνει <em>θεωρητικά</em> τις περισσότερες μισοτελειωμένες/κατεστραμμένες μεταφορτώσεις, αλλά δεν αντικαθιστά τον έλεγχο με το turbo απενεργοποιημένο μετέπειτα\">έλεγχος ημερομηνίας",

		"cut_u2sz": "μέγεθος (σε MiB) κάθε κομματιού μεταφόρτωσης; μεγάλες τιμές λειτουργούν καλύτερα σε μεγαλύτερες αποστάσεις διακομιστή-πελάτη. Δοκίμασε μικρές τιμές σε πολύ άστατες συνδέσεις",

		"cut_flag": "εξασφαλίζει ότι μόνο μία καρτέλα μεταφορτώνει κάθε φορά $N -- οι άλλες καρτέλες πρέπει να το έχουν κι αυτές ενεργό $N -- επηρεάζει μόνο τις καρτέλες που βρίσκονται στο ίδιο διεύθυνση",

		"cut_az": "μεταφόρτωσε τα αρχεία αλφαβητικά, αντί για το μικρότερο αρχείο, πρώτα$N$Nη αλφαβητική σειρά βοηθά να καταλάβεις αν κάτι χάλασε στο διακομιστή αλλά κάνει το ανέβασμα λίγο πιο αργό σε fiber / LAN",

		"cut_nag": "ειδοποίηση λειτουργικού συστήματος όταν τελειώσει η μεταφόρτωση$N(μόνο αν ο browser ή η καρτέλα δεν είναι ενεργά)",
		"cut_sfx": "ηχητική ειδοποίηση όταν τελειώσει η μεταφόρτωση$N(μόνο αν ο browser ή η καρτέλα δεν είναι ενεργά)",

		"cut_mt": "χρησιμοποίησε multithreading για να επιταχύνεις το hashing των αρχείων$N$Nχρησιμοποιεί web-workers και χρειάζεται$Nπερισσότερη RAM (μέχρι 512 MiB επιπλέον)$N$Nκάνει το https 30% πιο γρήγορο, το http 4.5x πιο γρήγορο\">mt",

		"cut_wasm": "χρησιμοποίησε wasm αντί για τον ενσωματωμένο hasher του browser; βελτιώνει την ταχύτητα σε chrome-based browsers αλλά αυξάνει το φορτίο της CPU, και παλιές εκδόσεις chrome έχουν bugs που κάνουν το browser να τρώει όλη τη RAM και να κρασάρει αν ενεργοποιηθεί\">wasm",

		"cft_text": "κείμενο favicon (κενό και ανανέωση για απενεργοποίηση)",
		"cft_fg": "χρώμα προσκηνίου",
		"cft_bg": "χρώμα παρασκηνίου",

		"cdt_lim": "μέγιστος αριθμός αρχείων προς εμφάνιση σε ένα φάκελο",
		"cdt_ask": "όταν φτάνεις στο τέλος,$Nαντί να φορτώσει περισσότερα αρχεία,$Nρωτά τι να κάνει",
		"cdt_hsort": "πόσους κανόνες ταξινόμησης (&lt;code&gt;,sorthref&lt;/code&gt;) να συμπεριλάβει σε URLs πολυμέσων. Αν το βάλεις 0 αγνοεί και κανόνες ταξινόμησης στους συνδέσμους πολυμέσων",

		"tt_entree": "εμφάνιση navpane (δέντρο διαδρομών)$NΠλήκτρο συντόμευσης: B",
		"tt_detree": "εμφάνιση breadcrumbs (καρτέλες διαδρομών)$NΠλήκτρο συντόμευσης: B",
		"tt_visdir": "κύλιση στον επιλεγμένο φάκελο",
		"tt_ftree": "εναλλαγή δέντρου διαδρομών / αρχείων κειμένου$NΠλήκτρο συντόμευσης: V",
		"tt_pdock": "εμφάνιση γονικών φακέλων σε σταθερή μπάρα επάνω",
		"tt_dynt": "αυτόματη επέκταση καθώς επεκτείνεται το δέντρο διαδρομών",
		"tt_wrap": "αναδίπλωση λέξεων",
		"tt_hover": "αποκάλυψη των γραμμών που ξεπερνούν το πλάτος με το ποντίκι πάνω τους$N( σπάει το scroll εκτός αν το ποντίκι $N&nbsp; είναι στην αριστερή στήλη )",

		"ml_pmode": "στο τέλος του φακέλου...",
		"ml_btns": "εντολές",
		"ml_tcode": "μετακωδικοποίηση",
		"ml_tcode2": "μετακωδικοποίηση σε",
		"ml_tint": "φίλτρο χρώματος",
		"ml_eq": "ισοσταθμιστής ήχου",
		"ml_drc": "συμπιεστής δυναμικής εμβέλειας",

		"mt_loop": "επανάληψη ενός τραγουδιού\">🔁",
		"mt_one": "σταμάτα μετά από ένα τραγούδι\">1️⃣",
		"mt_shuf": "τυχαία σειρά τραγουδιών σε κάθε φάκελο\">🔀",
		"mt_aplay": "αυτόματη αναπαραγωγή αν υπάρχει song-ID στη διεύθυνση που μπήκες στο διακομιστή$N$Nη απενεργοποίηση αυτού, σταματά το URL από το να ενημερώνεται με τα song-ID ενώ παίζει η μουσική για να αποτραπεί η αυτόματη αναπαραγωγή αν χαθούν αυτές οι ρυθμίσεις αλλά το URL παραμείνει το ίδιο\">a▶",
		"mt_preload": "ξεκίνα  τη φόρτωση του επόμενου τραγουδιού κοντά στο τέλος για συνεχόμενη ακρόαση\">προφόρτωση",
		"mt_prescan": "πήγαινε στον επόμενο φάκελο πριν τελειώσει το τελευταίο τραγούδι$Nγια να μη σταματήσει το πρόγραμμα περιήγησης να παίζει μουσική\">nav",
		"mt_fullpre": "προσπάθησε να προφορτώσεις ολόκληρο το τραγούδι;$N✅ ενεργό σε <b>αναξιόπιστες</b> συνδέσεις,$N❌ πιθανότατα απενεργοποιημένο σε αργές συνδέσεις\">πλήρες",
		"mt_fau": "σε κινητά, πρόλαβε να μην σταματήσει η μουσική αν το επόμενο τραγούδι δεν προφορτώθηκε γρήγορα (μπορεί να προκαλέσει πρόβλημα στην εμφάνιση των ετικετών)\">☕️",
		"mt_waves": "γραμμή αναζήτησης κυματομορφής:$Nεμφάνιση έντασης ήχου στην μπάρα αναζήτησης\">~s",
		"mt_npclip": "εμφάνισε κουμπιά για αντιγραφή του τρέχοντος τραγουδιού\">/np",
		"mt_m3u_c": "εμφάνισε κουμπιά για αντιγραφή των$Nεπιλεγμένων τραγουδιών ως καταχωρήσεις λίστας m3u8\">📻",
		"mt_octl": "ενσωμάτωση στο λειτουργικό σύστημα (σηντομεύσεις πλήκτρων πολυμέσων / osd)\">έλεγχος-OS",
		"mt_oseek": "επιτρέπει την αναζήτηση μέσω ενσωμάτωσης του λειτουργικού συστήματος$N$Nσημείωση: σε μερικές συσκευές (iPhones),$Nαντικαθιστά το κουμπί επόμενου τραγουδιού\">αναζήτηση",
		"mt_oscv": "εμφάνιση εξωφύλλου άλμπουμ σε osd\">εξώφυλλο",
		"mt_follow": "κρατά το τρέχον κομμάτι ορατό κατά την κύλιση\">🎯",
		"mt_compact": "συμπαγή κουμπιά ελέγχου\">⟎",
		"mt_uncache": "καθάρισε την προσωρινή μνήμη &nbsp;(δοκίμασε αυτό αν ο browser έχει αποθηκεύσει$Nχαλασμένο αντίγραφο τραγουδιού και αρνείται να παίξει)\">εκκαθάριση",
		"mt_mloop": "τυχαία αναπαραγωγή στον ανοικτό φάκελο\">🔁 τυχαία αναπαραγωγή",
		"mt_mnext": "φόρτωση επόμενου φακέλου και συνέχιση\">📂 επόμενο",
		"mt_mstop": "σταμάτησε την αναπαραγωγή\">⏸ σταμάτημα",
		"mt_cflac": "μετατροπή flac / wav σε {0}\">flac",
		"mt_caac": "μετατροπή aac / m4a σε {0}\">aac",
		"mt_coth": "μετατροπή όλων των άλλων (εκτός των mp3) σε {0}\">άλλο",
		"mt_c2opus": "καλύτερη επιλογή για desktop, laptop, android\">opus",
		"mt_c2owa": "opus-weba, για iOS 17.5 και νεότερα\">owa",
		"mt_c2caf": "opus-caf, για iOS 11 έως 17\">caf",
		"mt_c2mp3": "χρησιμοποίησε αυτό σε πολύ παλιές συσκευές\">mp3",
		"mt_c2flac": "βέλτιστη ποιότητα ήχου αλλά τεράστιο αρχείο για μεταφόρτωση\">flac",
		"mt_c2wav": "ασυμπίεστη αναπαραγωγή (ακόμα μεγαλύτερο αρχείο)\">wav",
		"mt_c2ok": "μια χαρά, σοφή επιλογή",
		"mt_c2nd": "δεν είναι η προτεινόμενη μορφή εξόδου για τη συσκευή σου, αλλά αυτό είναι ok",
		"mt_c2ng": "η συσκευή σου φαίνεται να μην υποστηρίζει αυτήν τη μορφή εξόδου, αλλά ας το δοκιμάσουμε ούτως ή άλλως",
		"mt_xowa": "υπάρχουν bugs σε iOS που εμποδίζουν την αναπαραγωγή στο παρασκήνιο με αυτήν τη μορφή· χρησιμοποίησε caf ή mp3 αντ’ αυτού",
		"mt_tint": "επίπεδο φόντου (0-100) στην μπάρα αναζήτησης$Nγια να κάνεις το buffering λιγότερο ενοχλητικό",
		"mt_eq": "ενεργοποιεί τον ισοσταθμιστή και τον έλεγχο ενίσχυσης;$N$Nενίσχυση &lt;code&gt;0&lt;/code&gt; = στάνταρ 100% ένταση (απαράλλαχτη)$N$Nεύρος &lt;code&gt;1 &nbsp;&lt;/code&gt; = στάνταρ στερεοφωνικό (απαράλλαχτο)$Nεύρος &lt;code&gt;0.5&lt;/code&gt; = 50% αριστερά-δεξιά μίξη ήχου$Nεύρος &lt;code&gt;0 &nbsp;&lt;/code&gt; = μονοφωνικό$N$Nενίσχυση &lt;code&gt;-0.8&lt;/code&gt; &amp; εύρος &lt;code&gt;10&lt;/code&gt; = αφαίρεση φωνής :^)$N$Nη ενεργοποίηση του ισοσταθμιστή κάνει τα άλμπουμ χωρίς κενά, να παίζουν χωρίς καθόλου κενά, οπότε άφησέ το ενεργό με όλες τις τιμές στο μηδέν (εκτός από εύρος = 1) αν σε νοιάζει",
		"mt_drc": "ενεργοποιεί τον συμπιεστή δυναμικής εμβέλειας (εξομάλυνση έντασης / ακραία συμπίεση έντασης); θα ενεργοποιήσει και τον ισοσταθμιστή για να ισορροπήσει τον ήχο, οπότε βάλε όλα τα πεδία ισοσταθμιστή εκτός από το 'εύρος' στο 0 αν δεν το θες$N$Nχαμηλώνει την ένταση του ήχου πάνω από το όριο (THRESHOLD) dB; για κάθε RATIO dB πέρα από το όριο υπάρχει 1 dB εξόδου, οπότε οι προεπιλεγμένες τιμές όριο -24 και 'λόγος' 12 σημαίνουν ότι δεν θα ξεπεράσει ποτέ τα -22 dB και είναι ασφαλές να αυξήσεις την ενίσχυση ισοσταθμιστή σε 0.8, ή και 1.8 με ATK 0 και μεγάλο RLS όπως 90 (δουλεύει μόνο σε firefox· το RLS είναι max 1 σε άλλους browsers)$N$N(δες wikipedia, το εξηγούν καλύτερα)",

		"mb_play": "παίξε",
		"mm_hashplay": "να παίξω αυτό το αρχείο ήχου;",
		"mm_m3u": "πάτα <code>Enter/Εντάξει</code> για Αναπαραγωγή\nπάτα <code>ESC/Άκυρο</code> για Επεξεργασία",
		"mp_breq": "χρειάζεται firefox 82+ ή chrome 73+ ή iOS 15+",
		"mm_bload": "φορτώνει...",
		"mm_bconv": "μετατροπή σε {0}, περίμενε...",
		"mm_opusen": "ο browser σου δεν παίζει αρχεία aac / m4a;\nη μετατροπή σε opus είναι τώρα ενεργή",
		"mm_playerr": "η αναπαραγωγή, απέτυχε: ",
		"mm_eabrt": "Η προσπάθεια αναπαραγωγής ακυρώθηκε",
		"mm_enet": "Η σύνδεση του ίντερνέτ σου είναι χάλια",
		"mm_edec": "Το αρχείο αυτό είναι μάλλον κατεστραμμένο;;",
		"mm_esupp": "Ο browser σου δεν καταλαβαίνει αυτή τη μορφή ήχου",
		"mm_eunk": "Άγνωστο σφάλμα",
		"mm_e404": "Αδύνατη η αναπαραγωγή ήχου; σφάλμα 404: Το αρχείο δεν βρέθηκε.",
		"mm_e403": "Αδύνατη η αναπαραγωγή ήχου; σφάλμα 403: Άρνηση πρόσβασης.\n\nΔοκίμασε F5 για επαναφόρτωση, ίσως να έχεις αποσυνδεθεί",
		"mm_e500": "Αδύνατη η αναπαραγωγή ήχου; σφάλμα 500: Έλεγξε τα logs του διακομιστή.",
		"mm_e5xx": "Αδύνατη η αναπαραγωγή ήχου; σφάλμα διακομιστή",
		"mm_nof": "δεν βρέθηκαν άλλα αρχεία ήχου τριγύρω",
		"mm_prescan": "Αναζήτηση μουσικής για επόμενο τραγούδι...",
		"mm_scank": "Βρέθηκε το επόμενο τραγούδι:",
		"mm_uncache": "κρυφή μνήμη καθαρίστηκε· όλα τα τραγούδια θα ξανακατεβούν στην επόμενη αναπαραγωγή",
		"mm_hnf": "το τραγούδι αυτό πλέον δεν υπάρχει",

		"im_hnf": "η εικόνα αυτή πλέον δεν υπάρχει",

		"f_empty": "αυτός ο φάκελος είναι άδειος",
		"f_chide": "αυτό θα κρύψει τη στήλη «{0}»\n\nμπορείς να εμφανίσεις τις στήλες από τις ρυθμίσεις",
		"f_bigtxt": "αυτό το αρχείο είναι {0} MiB σε μέγεθος — σίγουρα θέλεις να το δεις ως κείμενο;",
		"f_bigtxt2": "να δεις μόνο το τέλος του αρχείου αντί για όλο; αυτό ενεργοποιεί και το following/tailing, που δείχνει νέες γραμμές που προστίθενται ζωντανά",
		"fbd_more": '<div id="blazy">εμφανίζονται <code>{0}</code> από <code>{1}</code> αρχεία; <a href="#" id="bd_more">δείξε {2}</a> ή <a href="#" id="bd_all">δείξε τα όλα</a></div>',
		"fbd_all": '<div id="blazy">εμφανίζονται <code>{0}</code> από <code>{1}</code> αρχεία; <a href="#" id="bd_all">δείξε όλα</a></div>',
		"f_anota": "μόνο {0} από τα {1} αντικείμενα επιλέχθηκαν;\nγια να επιλέξεις ολόκληρο το φάκελο, κύλησε πρώτα μέχρι κάτω",

		"f_dls": 'οι σύνδεσμοι αρχείων στον τρέχοντα φάκελο έχουν\nμετατραπεί σε συνδέσμους λήψης',

		"f_partial": "Για να κατεβάσεις με ασφάλεια ένα αρχείο που ανεβαίνει, κλίκαρε το αρχείο με το ίδιο όνομα, αλλά χωρίς την κατάληξη <code>.PARTIAL</code>. Πάτα Άκυρο ή Escape για να σταματήσεις.\n\nΠάτα Εντάξει / Enter αν αγνοείς την προειδοποίηση και κατέβασε το <code>.PARTIAL</code> αρχείο, που σχεδόν σίγουρα θα είναι κατεστραμμένο.",

		"ft_paste": "επικόλλησε {0} αντικείμενα$NΠλήκτρο συντόμευσης: ctrl-V",
		"fr_eperm": 'δεν μπορεί να μετονομαστεί:\nδεν έχεις δικαίωμα “μετακίνησης” σε αυτόν το φάκελο',
		"fd_eperm": 'δεν μπορεί να διαγραφεί:\nδεν έχεις δικαίωμα “διαγραφής” σε αυτόν το φάκελο',
		"fc_eperm": 'δεν μπορεί να κοπεί:\nδεν έχεις δικαίωμα “μετακίνησης” σε αυτόν το φάκελο',
		"fp_eperm": 'δεν μπορεί να επικολληθεί:\nδεν έχεις δικαίωμα “εγγραφής” σε αυτόν το φάκελο',
		"fr_emore": "επίλεξε τουλάχιστον ένα αντικείμενο για μετονομασία",
		"fd_emore": "επίλεξε τουλάχιστον ένα αντικείμενο για διαγραφή",
		"fc_emore": "επίλεξε τουλάχιστον ένα αντικείμενο για αποκοπή",
		"fcp_emore": "επίλεξε τουλάχιστον ένα αντικείμενο για αντιγραφή στο πρόχειρο",

		"fs_sc": "μοιράσου το φάκελο που βρίσκεσαι",
		"fs_ss": "μοιράσου τα επιλεγμένα αρχεία",
		"fs_just1d": "δεν μπορείς να επιλέξεις περισσότερους από έναν φακέλους,\nή να αναμείξεις αρχεία και φακέλους στην ίδια επιλογή",
		"fs_abrt": "❌ ακύρωση",
		"fs_rand": "🎲 τυχαίο όνομα",
		"fs_go": "✅ δημιούργησε κοινή χρήση",
		"fs_name": "όνομα",
		"fs_src": "πηγή",
		"fs_pwd": "κωδικός",
		"fs_exp": "λήξη",
		"fs_tmin": "λεπτά",
		"fs_thrs": "ώρες",
		"fs_tdays": "ημέρες",
		"fs_never": "αιώνιο",
		"fs_pname": "προαιρετικό όνομα συνδέσμου; αν είναι κενό, θα είναι τυχαίο",
		"fs_tsrc": "το αρχείο ή ο φάκελος προς κοινή χρήση",
		"fs_ppwd": "προαιρετικός κωδικός",
		"fs_w8": "δημιουργία κοινής χρήσης...",
		"fs_ok": "πάτα <code>Enter/Εντάξει</code> για Πρόχειρο\nπάτα <code>ESC/Άκυρο</code> για Κλείσιμο",

		"frt_dec": "μπορεί να διορθώσει μερικές περιπτώσεις κατεστραμμένων ονομάτων αρχείων\">αποκωδικοποίηση url",
		"frt_rst": "επανέφερε τα ονόματα αρχείων στα αρχικά τους\">↺ επαναφορά",
		"frt_abrt": "ακύρωσε και κλείσε αυτό το παράθυρο\">❌ ακύρωση",
		"frb_apply": "ΕΦΑΡΜΟΓΗ ΜΕΤΟΝΟΜΑΣΙΑΣ",
		"fr_adv": "μαζική / μεταδεδομένα / μετονομασία με πρότυπα\">προχωρημένη",
		"fr_case": "regex με διάκριση πεζών/κεφαλαίων\">case",
		"fr_win": "ασφαλή ονόματα για windows; αντικαθιστά <code>&lt;&gt;:&quot;\\|?*</code> με ιαπωνικούς χαρακτήρες πλήρους πλάτους\">win",
		"fr_slash": "αντικαθίσταται <code>/</code> με χαρακτήρα που δεν δημιουργεί νέους φακέλους\">όχι /",
		"fr_re": "μοτίβα αναζήτησης (regex) για αναζήτηση στα αρχικά ονόματα; τα καταγραφόμενα groups μπορούν να χρησιμοποιηθούν στο πεδίο μορφοποίησης παρακάτω όπως &lt;code&gt;(1)&lt;/code&gt; και &lt;code&gt;(2)&lt;/code&gt; και ούτω καθεξής",
		"fr_fmt": "εμπνευσμένο από foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; αντικαθίσταται από τίτλο τραγουδιού,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; παραλείπει το [this] αν το artist είναι κενό$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; γεμίζει τον αριθμό κομματιού σε 2 ψηφία",
		"fr_pdel": "διαγραφή",
		"fr_pnew": "αποθήκευση ως",
		"fr_pname": "δώσε όνομα για τη νέα προεπιλογή",
		"fr_aborted": "ακυρώθηκε",
		"fr_lold": "παλιό όνομα",
		"fr_lnew": "νέο όνομα",
		"fr_tags": "ετικέτες για τα επιλεγμένα αρχεία (μόνο για ανάγνωση):",
		"fr_busy": "μετονομασία {0} αντικειμένων...\n\n{1}",
		"fr_efail": "αποτυχία μετονομασίας:\n",
		"fr_nchg": "{0} από τα νέα ονόματα άλλαξαν λόγω <code>win</code> και/ή <code>όχι /</code>\n\nΕίναι ΟΚ να συνεχίσουμε με αυτά τα ονόματα;",

		"fd_ok": "διαγραφή OK",
		"fd_err": "αποτυχία διαγραφής:\n",
		"fd_none": "δεν διαγράφηκε τίποτα; ίσως μπλοκαρισμένο από τις ρυθμίσεις του διακομιστή (xbd);",
		"fd_busy": "διαγραφή {0} αντικειμένων...\n\n{1}",
		"fd_warn1": "ΔΙΑΓΡΑΦΗ αυτών των {0} αντικειμένων;",
		"fd_warn2": "<b>Τελευταία ευκαιρία!</b> Δεν υπάρχει αναίρεση. Διαγραφή;",

		"fc_ok": "αποκοπή {0} αντικειμένων",
		"fc_warn": 'αποκοπή {0} αντικειμένων\n\nαλλά: μόνο <b>αυτή</b> η καρτέλα browser μπορεί να τα επικολλήσει\n(λόγω πολύ μεγάλης επιλογής)',

		"fcc_ok": "αντιγράφηκαν {0} αντικείμενα στο πρόχειρο",
		"fcc_warn": "αντιγράφηκαν {0} αντικείμενα στο πρόχειρο\n\nαλλά: μόνο <b>αυτή</b> η καρτέλα browser μπορεί να τα επικολλήσει\n(λόγω πολύ μεγάλης επιλογής)",

		"fp_apply": "χρησιμοποίησε αυτά τα ονόματα",
		"fp_ecut": "πρώτα κάνε αποκοπή ή αντιγραφή κάποιων αρχείων / φακέλων για επικόλληση / μετακίνηση\n\nσημείωση: μπορείς να αποκόπτεις / επικολλάς ανάμεσα σε διαφορετικές καρτέλες browser",
		"fp_ename": "τα {0} αντικείμενα δεν μπορούν να μετακινηθούν εδώ γιατί τα ονόματα υπάρχουν ήδη. Δώσε νέα ονόματα παρακάτω για να συνεχίσεις, ή άφησε κενό για να τα αγνοήσεις:",
		"fcp_ename": "τα {0} αντικείμενα δεν μπορούν να αντιγραφούν εδώ γιατί τα ονόματα υπάρχουν ήδη. Δώσε νέα ονόματα παρακάτω για να συνεχίσεις, ή άφησε κενό για να τα αγνοήσεις:",
		"fp_emore": "υπάρχουν ακόμα συγκρούσεις ονομάτων που πρέπει να διορθωθούν",
		"fp_ok": "μετακίνηση OK",
		"fcp_ok": "αντιγραφή OK",
		"fp_busy": "μετακίνηση {0} αντικειμένων...\n\n{1}",
		"fcp_busy": "αντιγραφή {0} αντικειμένων...\n\n{1}",
		"fp_abrt": "γίνεται ακύρωση...", //m
		"fp_err": "αποτυχία μετακίνησης:\n",
		"fcp_err": "αποτυχία αντιγραφής:\n",
		"fp_confirm": "να μετακινηθούν αυτά τα {0} αντικείμενα εδώ;",
		"fcp_confirm": "να αντιγραφούν αυτά τα {0} αντικείμενα εδώ;",
		"fp_etab": "αποτυχία ανάγνωσης πρόχειρου από άλλη καρτέλα browser",
		"fp_name": "μεταφόρτωση αρχείου από τη συσκευή σου. Δώσε του όνομα:",
		"fp_both_m": '<h6>διάλεξε τι θα επικολλήσεις</h6><code>Enter</code> = Μετακίνηση {0} αρχείων από «{1}»\n<code>ESC</code> = Μεταφόρτωση {2} αρχείων από τη συσκευή σου',
		"fcp_both_m": '<h6>διάλεξε τι θα επικολλήσεις</h6><code>Enter</code> = Αντιγραφή {0} αρχείων από «{1}»\n<code>ESC</code> = Μεταφόρτωση {2} αρχείων από τη συσκευή σου',
		"fp_both_b": '<a href="#" id="modal-ok">Μετακίνηση</a><a href="#" id="modal-ng">Μεταφόρτωση</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Αντιγραφή</a><a href="#" id="modal-ng">Μεταφόρτωση</a>',

		"mk_noname": "γράψε ένα όνομα στο πεδίο κειμένου αριστερά πριν το κάνεις :p",

		"tv_load": "Φόρτωση αρχείου κειμένου:\n\n{0}\n\n{1}% ({2} από {3} MiB φορτωμένα)",
		"tv_xe1": "αδυναμία φόρτωσης αρχείου κειμένου:\n\nσφάλμα ",
		"tv_xe2": "404, αρχείο δεν βρέθηκε",
		"tv_lst": "λίστα αρχείων κειμένου σε",
		"tvt_close": "επιστροφή στην προβολή φακέλου$NΣυντόμευση: M (ή Esc)\">❌ κλείσιμο",
		"tvt_dl": "κατέβασε αυτό το αρχείο$NΣυντόμευση: Y\">💾 λήψη",
		"tvt_prev": "προβολή προηγούμενου εγγράφου$NΣυντόμευση: i\">⬆ προηγούμενο",
		"tvt_next": "προβολή επόμενου εγγράφου$NΣυντόμευση: K\">⬇ επόμενο",
		"tvt_sel": "επέλεξε αρχείο &nbsp; (για αποκοπή / αντιγραφή / διαγραφή / ...)$NΣυντόμευση: S\">επιλογή",
		"tvt_edit": "άνοιγμα αρχείου στον επεξεργαστή κειμένου$NΣυντόμευση: E\">✏️ επεξεργασία",
		"tvt_tail": "παρακολούθηση αρχείου για αλλαγές; εμφάνιση νέων γραμμών σε πραγματικό χρόνο\">📡 παρακολούθηση",
		"tvt_wrap": "αναδίπλωση λέξεων\">↵",
		"tvt_atail": "κλείδωμα κύλισης στο κάτω μέρος\">⚓",
		"tvt_ctail": "αποκωδικοποίηση χρωμάτων τερματικού (ansi escape codes)\">🌈",
		"tvt_ntail": "όριο κύλισης (πόσα bytes κειμένου να κρατούνται φορτωμένα)",

		"m3u_add1": "το τραγούδι προστέθηκε στη λίστα m3u",
		"m3u_addn": "προστέθηκαν {0} τραγούδια στη λίστα m3u",
		"m3u_clip": "η λίστα m3u αντιγράφηκε στο πρόχειρο\n\nπρέπει να φτιάξεις ένα νέο αρχείο κειμένου με όνομα η_λίστα_μου.m3u και να επικολλήσεις τη λίστα μέσα· αυτό θα το καταστήσει αναπαράξιμο",

		"gt_vau": "μην δείχνεις το βίντεο, παίξε μόνο τον ήχο\">🎧",
		"gt_msel": "ενεργοποίηση επιλογής αρχείων; ctrl-κλικ σε αρχείο για παράκαμψη$N$N&lt;em&gt;όταν είναι ενεργό: διπλό κλικ σε αρχείο / φάκελο το ανοίγει&lt;/em&gt;$N$NΣυντόμευση: S\">πολλαπλή επιλογή",
		"gt_crop": "κεντραρισμένη περικοπή μικρογραφιών\">περικοπή",
		"gt_3x": "μικρογραφίες υψηλής ανάλυσης\">3x",
		"gt_zoom": "ζουμ",
		"gt_chop": "κόψε",
		"gt_sort": "ταξινόμηση κατά",
		"gt_name": "όνομα",
		"gt_sz": "μέγεθος",
		"gt_ts": "ημερομηνία",
		"gt_ext": "τύπος",
		"gt_c1": "μεγαλύτερη περικοπή ονομάτων αρχείων (δείξε λιγότερα)",
		"gt_c2": "μικρότερη περικοπή ονομάτων αρχείων (δείξε περισσότερα)",

		"sm_w8": "αναζήτηση...",
		"sm_prev": "τα παρακάτω αποτελέσματα αναζήτησης προέρχονται από προηγούμενη αναζήτηση:\n  ",
		"sl_close": "κλείσιμο αποτελεσμάτων αναζήτησης",
		"sl_hits": "εμφανίζονται {0} αποτελέσματα",
		"sl_moar": "φόρτωσε περισσότερα",

		"s_sz": "μέγεθος",
		"s_dt": "ημερομηνία",
		"s_rd": "μονοπάτι",
		"s_fn": "όνομα",
		"s_ta": "ετικέτες",
		"s_ua": "ανέβηκε@",
		"s_ad": "προχωρ.",
		"s_s1": "ελάχιστο σε MiB",
		"s_s2": "μέγιστο σε MiB",
		"s_d1": "ελάχιστο iso8601",
		"s_d2": "μέγιστο iso8601",
		"s_u1": "μεταφορτώθηκε αργότερα",
		"s_u2": "και/ή πριν",
		"s_r1": "το μονοπάτι περιέχει &nbsp; (χωρισμένα με κενό)",
		"s_f1": "το όνομα περιέχει &nbsp; (άρνηση με -nope)",
		"s_t1": "οι ετικέτες περιέχουν &nbsp; (^=αρχή, τέλος=$)",
		"s_a1": "συγκεκριμένες ιδιότητες μεταδεδομένων",

		"md_eshow": "δεν μπορεί να εμφανιστεί ",
		"md_off": "[📜<em>readme</em>] απενεργοποιημένο στο [⚙️] -- κρυμμένο έγγραφο",

		"badreply": "Αποτυχία ανάλυσης απάντησης από το διακομιστή",

		"xhr403": "403: Πρόσβαση αρνήθηκε\n\nδοκίμασε το F5, ίσως αποσυνδέθηκες",
		"xhr0": "άγνωστο (πιθανόν αποσύνδεση από το διακομιστή ή ο διακομιστής είναι εκτός σύνδεσης)",
		"cf_ok": "συγγνώμη γι' αυτό -- η προστασία DD" + wah + "oS ενεργοποιήθηκε\n\nοι διαδικασίες θα συνεχιστούν σε περίπου 30 δευτερόλεπτα\n\nαν δεν γίνει τίποτα, πάτα F5 για επαναφόρτωση",
		"tl_xe1": "αδύνατη η λίστα υποφακέλων:\n\nσφάλμα ",
		"tl_xe2": "404: Ο φάκελος δεν βρέθηκε",
		"fl_xe1": "αδύνατη η λίστα αρχείων σε φάκελο:\n\nσφάλμα ",
		"fl_xe2": "404: Ο φάκελος δεν βρέθηκε",
		"fd_xe1": "αδύνατη η δημιουργία υποφακέλου:\n\nσφάλμα ",
		"fd_xe2": "404: Ο γονικός φάκελος δεν βρέθηκε",
		"fsm_xe1": "αδύνατη η αποστολή μηνύματος:\n\nσφάλμα ",
		"fsm_xe2": "404: Ο γονικός φάκελος δεν βρέθηκε",
		"fu_xe1": "αποτυχία φόρτωσης λίστας unpost από το διακομιστή:\n\nσφάλμα ",
		"fu_xe2": "404: Το αρχείο δεν βρέθηκε??",

		"fz_tar": "μη συμπιεσμένο αρχείο gnu-tar (linux / mac)",
		"fz_pax": "μη συμπιεσμένο pax-format tar (πιο αργό)",
		"fz_targz": "gnu-tar με συμπίεση gzip επίπεδο 3$N$Nσυνήθως πολύ αργό, οπότε$Nχρησιμοποίησε καλύτερα μη συμπιεσμένο tar",
		"fz_tarxz": "gnu-tar με συμπίεση xz επίπεδο 1$N$Nσυνήθως πολύ αργό, οπότε$Nχρησιμοποίησε καλύτερα μη συμπιεσμένο tar",
		"fz_zip8": "zip με ονόματα αρχείων utf8 (ίσως να κολλάει σε windows 7 και παλιότερα)",
		"fz_zipd": "zip με παραδοσιακά ονόματα cp437, για πολύ παλιό λογισμικό",
		"fz_zipc": "cp437 με crc32 υπολογισμένο νωρίτερα,$Nγια MS-DOS PKZIP v2.04g (οκτώβριος 1993)$N(παίρνει παραπάνω χρόνο πριν ξεκινήσει η μεταφόρτωση)",

		"un_m1": "μπορείς να διαγράψεις τα πρόσφατα αρχεία που μεταφόρτωσες (ή να ακυρώσεις τα μισοτελειωμένα) παρακάτω",
		"un_upd": "ανανέωση",
		"un_m4": "ή μοιράσου τα αρχεία που βλέπεις παρακάτω:",
		"un_ulist": "εμφάνιση",
		"un_ucopy": "αντιγραφή",
		"un_flt": "προαιρετικό φίλτρο:&nbsp; η διεύθυνση πρέπει να περιέχει",
		"un_fclr": "καθαρισμός φίλτρου",
		"un_derr": "αποτυχία διαγραφής unpost:\n",
		"un_f5": "κάτι χάλασε, δοκίμασε την ανανέωση ή πάτα F5",
		"un_uf5": "συγγνώμη αλλά πρέπει να ανανεώσεις τη σελίδα (πχ με F5 ή CTRL-R) πριν ακυρώσεις αυτήν την αποστολή",
		"un_nou": "<b>προσοχή:</b> ο διακομιστής είναι πολύ φορτωμένος για να δείξει μισοτελειωμένες αποστολές· πάτα την ανανέωση, σε λίγο",
		"un_noc": "<b>προσοχή:</b> το unpost των ολοκληρωμένων αρχείων δεν επιτρέπεται από τη ρύθμιση του διακομιστή",
		"un_max": "εμφανίζονται τα πρώτα 2000 αρχεία (χρησιμοποίησε φίλτρο)",
		"un_avail": "μπορείς να διαγράψεις {0} πρόσφατα αρχεία<br />μπορείς να ακυρώσεις {1} μισοτελειωμένες αποστολές",
		"un_m2": "ταξινομημένα κατά χρόνο μεταφόρτωσης; τα πιο πρόσφατα πρώτα:",
		"un_no1": "άκυρο! καμία μεταφόρτωση δεν είναι αρκετά πρόσφατη",
		"un_no2": "άκυρο! καμία μεταφόρτωση με αυτό το φίλτρο δεν είναι αρκετά πρόσφατη",
		"un_next": "διάγραψε τα επόμενα {0} αρχεία παρακάτω",
		"un_abrt": "άκυρο",
		"un_del": "διαγραφή",
		"un_m3": "φορτώνω τις πρόσφατες μεταφορτώσεις σου...",
		"un_busy": "διαγράφω {0} αρχεία...",
		"un_clip": "αντιγράφηκαν {0} σύνδεσμοι στο πρόχειρο",

		"u_https1": "πρέπει",
		"u_https2": "μετάβαση σε https",
		"u_https3": "για καλύτερη απόδοση",
		"u_ancient": 'ο browser σου είναι εντυπωσιακά απαρχαιωμένος — ίσως να <a href="#" onclick="goto(\'bup\')">χρησιμοποιήσεις το bup αντί γι\' αυτό</a>',
		"u_nowork": "χρειάζεται firefox 53+ ή chrome 57+ ή iOS 11+",
		"tail_2old": "χρειάζεται firefox 105+ ή chrome 71+ ή iOS 14.5+",
		"u_nodrop": "ο browser σου είναι πολύ παλιός για drag&amp;drop μεταφορτώσεις",
		"u_notdir": "αυτός δεν είναι φάκελος!\n\nο browser σου είναι πολύ παλιός,\nδοκίμασε drag&amp;drop αντ' αυτού",
		"u_uri": "για να κάνεις drag&amp;drop εικόνων από άλλα παράθυρα browser,\nρίξ' τες πάνω στο μεγάλο κουμπί μεταφόρτωσης",
		"u_enpot": 'άλλαξε στο <a href="#">potato UI</a> (ίσως ανεβάζει πιο γρήγορα)',
		"u_depot": 'άλλαξε στο <a href="#">fancy UI</a> (ίσως ανεβάζει πιο αργά)',
		"u_gotpot": "αλλάζω στο potato UI για πιο γρήγορη μεταφόρτωση,\n\nμπορείς να το αλλάξεις πάλι αν θες!",
		"u_pott": "<p>αρχεία: &nbsp; <b>{0}</b> ολοκληρωμένα, &nbsp; <b>{1}</b> αποτυχημένα, &nbsp; <b>{2}</b> σε εξέλιξη, &nbsp; <b>{3}</b> σε ουρά</p>",
		"u_ever": "αυτός είναι ο βασικός uploader; το up2k θέλει τουλάχιστον<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'αυτός είναι ο βασικός uploader; το <a href="#" id="u2yea">up2k</a> είναι καλύτερο',
		"u_uput": "βελτιστοποίηση για ταχύτητα (παράλειψη ελέγχου ακεραιότητας)",
		"u_ewrite": "δεν έχεις δικαίωμα εγγραφής σε αυτόν τον φάκελο",
		"u_eread": "δεν έχεις δικαίωμα ανάγνωσης σε αυτόν τον φάκελο",
		"u_enoi": "η αναζήτηση αρχείων δεν είναι ενεργοποιημένη στο αρχείο ρυθμίσεων του διακομιστή",
		"u_enoow": "δεν μπορείς να κάνεις αντικατάσταση εδώ· χρειάζεται δικαίωμα Διαγραφής",
		"u_badf": "Αυτά τα {0} αρχεία (από {1} συνολικά) παραλείφθηκαν, πιθανώς λόγω δικαιωμάτων συστήματος αρχείων:\n\n",
		"u_blankf": "Αυτά τα {0} αρχεία (από {1} συνολικά) είναι άδεια / κενά· να τα μεταφορτώσω έτσι κι αλλιώς;\n\n",
		"u_applef": "Αυτά τα {0} αρχεία (από {1} συνολικά) πιθανώς δεν είναι επιθυμητά;\nΠάτα <code>Εντάξει/Enter</code> για ΝΑ ΑΓΝΟΗΘΟΥΝ τα παρακάτω αρχεία,\nΠάτα <code>Άκυρο/ESC</code> για ΝΑ ΜΗΝ ΑΠΟΚΛΕΙΣΤΟΥΝ και να ΜΕΤΑΦΟΡΤΩΘΟΎΝ κι αυτά:\n\n",
		"u_just1": "\nΊσως δουλέψει καλύτερα αν επιλέξεις μόνο ένα αρχείο",
		"u_ff_many": "αν χρησιμοποιείς <b>Linux / MacOS / Android,</b> τότε τόσα αρχεία <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>μπορεί</em> να κατάρρευση του Firefox!</a>\nαν γίνει αυτό, δοκίμασε ξανά (ή χρησιμοποίησε τον Chrome).",
		"u_up_life": "Αυτή η μεταφόρτωση θα διαγραφεί από το διακομιστή\n{0} μετά την ολοκλήρωσή της",
		"u_asku": "μεταφόρτωση αυτών των {0} αρχείων στο <code>{1}</code>",
		"u_unpt": "μπορείς να αναιρέσεις / διαγράψεις αυτήν τη μεταφόρτωση χρησιμοποιώντας το 🧯, πάνω αριστερά",
		"u_bigtab": "θα εμφανιστούν {0} αρχεία\n\nαυτό μπορεί να κάνει τον browser σου να κολλήσει, είσαι σίγουρος;",
		"u_scan": "Σάρωση αρχείων...",
		"u_dirstuck": "ο επεξεργαστής φακέλων κόλλησε προσπαθώντας να προσπελάσει τα εξής {0} αντικείμενα· θα τα παραλείψει:",
		"u_etadone": "Ολοκληρώθηκε ({0}, {1} αρχεία)",
		"u_etaprep": "(προετοιμασία για μεταφόρτωση)",
		"u_hashdone": "το hashing ολοκληρώθηκε",
		"u_hashing": "υπολογισμός hash",
		"u_hs": "handshaking...",
		"u_started": "τα αρχεία ανεβαίνουν τώρα· δες τα στο [🚀]",
		"u_dupdefer": "διπλότυπο; θα επεξεργαστεί μετά από όλα τα άλλα αρχεία",
		"u_actx": "πάτα αυτό το κείμενο για να μην χάσεις<br />απόδοση όταν αλλάζεις παράθυρα/καρτέλες",
		"u_fixed": "ΟΚ!&nbsp; Το διόρθωσα 👍",
		"u_cuerr": "αποτυχία μεταφόρτωσης τμήματοςς {0} από {1};\nπιθανώς ακίνδυνο, συνεχίζω\n\nαρχείο: {2}",
		"u_cuerr2": "ο διακομιστής απέρριψε τη μεταφόρτωση (τμήμα {0} από {1});\nθα ξαναδοκιμάσει αργότερα\n\nαρχείο: {2}\n\nσφάλμα ",
		"u_ehstmp": "θα ξαναδοκιμάσει; δες κάτω δεξιά",
		"u_ehsfin": "ο διακομιστής απέρριψε το αίτημα ολοκλήρωσης της μεταφόρτωσης; ξαναδοκιμάζει...",
		"u_ehssrch": "ο διακομιστής απέρριψε το αίτημα αναζήτησης; ξαναδοκιμάζει...",
		"u_ehsinit": "ο διακομιστής απέρριψε το αίτημα για εκκίνηση μεταφόρτωσης; ξαναδοκιμάζει...",
		"u_eneths": "σφάλμα δικτύου κατά το handshake μεταφόρτωσης; ξαναδοκιμάζει...",
		"u_enethd": "σφάλμα δικτύου κατά τον έλεγχο ύπαρξης στόχου; ξαναδοκιμάζει...",
		"u_cbusy": "ο διακομιστής περιμένει να μας εμπιστευτεί ξανά μετά από πρόβλημα δικτύου...",
		"u_ehsdf": "ο διακομιστής έμεινε από χώρο στο δίσκο!\n\nθα συνεχίσει να ξαναδοκιμάζει,\nσε περίπτωση που κάποιος\nελευθερώσει αρκετό χώρο για συνέχεια",
		"u_emtleak1": "φαίνεται πως ο browser σου έχει διαρροή μνήμης;\nπαρακαλώ",
		"u_emtleak2": ' <a href="{0}">αλλαγή σε https (συνιστάται)</a> ή ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'δοκίμασε τα εξής:\n<ul><li>πάτα <code>F5</code> για ανανέωση σελίδας</li><li>μετά απενεργοποίησε το &nbsp;<code>mt</code>&nbsp; κουμπί στις &nbsp;<code>⚙️ ρυθμίσεις</code></li><li>και δοκίμασε ξανά τη μεταφόρτωση</li></ul>Οι μεταφορτώσιες θα είναι λίγο πιο αργές, αλλά ok.\nΣυγγνώμη για την ταλαιπωρία!\n\nPS: το chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">έχει διόρθωση γι\' αυτό</a>',
		"u_emtleakf": 'δοκίμασε τα εξής:\n<ul><li>πάτα <code>F5</code> για ανανέωση σελίδας</li><li>μετά άνοιξε το <code>🥔</code> (potato) στο UI μεταφόρτωσης<li>και δοκίμασε ξανά τη μεταφόρτωση</li></ul>\nPS: ο firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">ελπίζει να φτιάξει αυτό το bug</a> κάποια στιγμή',
		"u_s404": "δεν βρέθηκε στο διακομιστή",
		"u_expl": "επεξήγηση",
		"u_maxconn": "οι περισσότεροι browser το περιορίζουν στα 6, αλλά ο firefox σου επιτρέπει να το αυξήσεις με <code>connections-per-server</code> στο <code>about:config</code>",
		"u_tu": '<p class="warn">ΠΡΟΕΙΔΟΠΟΙΗΣΗ: το turbo είναι ενεργοποιημένο, <span>&nbsp;το πρόγραμμα πελάτη ίσως να μην ανιχνεύσει και να μην ξαναεκκινήσει μισοτελειωμένες μεταφορτώσεις; δες τα tooltip του κουμπιού turbo</span></p>',
		"u_ts": '<p class="warn">ΠΡΟΕΙΔΟΠΟΙΗΣΗ: το turbo είναι ενεργοποιημένο, <span>&nbsp;τα αποτελέσματα αναζήτησης μπορεί να είναι λάθος; δες τα tooltip του κουμπιού turbo</span></p>',
		"u_turbo_c": "το turbo είναι απενεργοποιημένο στο αρχείο ρυθμίσεων του διακομιστή",
		"u_turbo_g": "απενεργοποιώ το turbo επειδή δεν έχεις δικαίωμα\nγια τη λίστα φακέλων σε αυτόν τον τόμο",
		"u_life_cfg": 'αυτόματη διαγραφή μετά από <input id="lifem" p="60" /> λεπτά (ή <input id="lifeh" p="3600" /> ώρες)',
		"u_life_est": 'η μεταφόρτωση θα διαγραφεί <span id="lifew" tt="τοπική ώρα">---</span>',
		"u_life_max": 'αυτός ο φάκελος επιβάλλει\nμέγιστη διάρκεια ζωής {0}',
		"u_unp_ok": "επιτρέπεται το unpost για {0}",
		"u_unp_ng": "δεν επιτρέπεται το unpost",
		"ue_ro": "έχεις μόνο δικαίωμα ανάγνωσης σε αυτόν το φάκελο\n\n",
		"ue_nl": "δεν είσαι συνδεδεμένος τώρα",
		"ue_la": 'είσαι συνδεδεμένος ως "{0}"',
		"ue_sr": "είσαι σε λειτουργία αναζήτησης αρχείων\n\nπήγαινε σε λειτουργία μεταφόρτωσης πατώντας το 🔎 (δίπλα στο μεγάλο κουμπί ΑΝΑΖΗΤΗΣΗΣ) και δοκίμασε πάλι\n\nσυγγνώμη",
		"ue_ta": "δοκίμασε να μεταφορτώσεις εκ νέου, θα πρέπει να δουλέψει τώρα",
		"ue_ab": "αυτό το αρχείο ανεβαίνει σε άλλο φάκελο και η μεταφόρτωση πρέπει να ολοκληρωθεί πριν ανέβει αλλού.\n\nΜπορείς να ακυρώσεις και να ξεχάσεις την αρχική μεταφόρτωση με το κουμπί 🧯 πάνω αριστερά",
		"ur_1uo": "ΟΚ: Το αρχείο ανέβηκε επιτυχώς",
		"ur_auo": "ΟΚ: Και τα {0} αρχεία ανέβηκαν επιτυχώς",
		"ur_1so": "ΟΚ: Το αρχείο βρέθηκε στο διακομιστή",
		"ur_aso": "ΟΚ: Και τα {0} αρχεία βρέθηκαν στο διακομιστή",
		"ur_1un": "Η μεταφόρτωση απέτυχε, συγγνώμη",
		"ur_aun": "Και οι {0} μεταφορτώσεις απέτυχαν, συγγνώμη",
		"ur_1sn": "Το αρχείο ΔΕΝ βρέθηκε στο διακομιστή",
		"ur_asn": "Τα {0} αρχεία ΔΕΝ βρέθηκαν στο διακομιστή",
		"ur_um": "Ολοκληρώθηκε;\n{0} μεταφορτώσεις είναι OK,\n{1} μεταφορτώσεις απέτυχαν, συγγνώμη",
		"ur_sm": "Ολοκληρώθηκε;\n{0} αρχεία βρέθηκαν στο διακομιστή,\n{1} αρχεία ΔΕΝ βρέθηκαν στο διακομιστή",

		"lang_set": "ανανέωση σελίδας για εφαρμογή της αλλαγής;"
	},
	"ita": {
		"tt": "Italiano",

		"cols": {
			"c": "pulsanti azione",
			"dur": "durata",
			"q": "qualità / bitrate",
			"Ac": "codec audio",
			"Vc": "codec video",
			"Fmt": "formato / container",
			"Ahash": "checksum audio",
			"Vhash": "checksum video",
			"Res": "risoluzione",
			"T": "tipo file",
			"aq": "qualità audio / bitrate",
			"vq": "qualità video / bitrate",
			"pixfmt": "subsampling / struttura pixel",
			"resw": "risoluzione orizzontale",
			"resh": "risoluzione verticale",
			"chs": "canali audio",
			"hz": "frequenza di campionamento"
		},

		"hks": [
			[
				"varie",
				["ESC", "chiudi vari elementi"],

				"file-manager",
				["G", "alterna vista lista / griglia"],
				["T", "alterna miniature / icone"],
				["⇧ A/D", "dimensione miniature"],
				["ctrl-K", "elimina selezionati"],
				["ctrl-X", "taglia selezione negli appunti"],
				["ctrl-C", "copia selezione negli appunti"],
				["ctrl-V", "incolla (sposta/copia) qui"],
				["Y", "scarica selezionati"],
				["F2", "rinomina selezionati"],

				"file-list-sel",
				["spazio", "alterna selezione file"],
				["↑/↓", "sposta cursore selezione"],
				["ctrl ↑/↓", "sposta cursore e viewport"],
				["⇧ ↑/↓", "seleziona file prec/succ"],
				["ctrl-A", "seleziona tutti i file / cartelle"],
			], [
				"navigation",
				["B", "alterna breadcrumb / pannello nav"],
				["I/K", "cartella prec/succ"],
				["M", "cartella genitore (o comprimi corrente)"],
				["V", "alterna cartelle / file di testo nel pannello nav"],
				["A/D", "dimensione pannello nav"],
			], [
				"audio-player",
				["J/L", "brano prec/succ"],
				["U/O", "salta 10sec indietro/avanti"],
				["0..9", "salta a 0%..90%"],
				["P", "play/pausa (avvia anche)"],
				["S", "seleziona brano in riproduzione"],
				["Y", "scarica brano"],
			], [
				"image-viewer",
				["J/L, ←/→", "immagine prec/succ"],
				["Home/End", "prima/ultima immagine"],
				["F", "schermo intero"],
				["R", "ruota in senso orario"],
				["⇧ R", "ruota in senso antiorario"],
				["S", "seleziona immagine"],
				["Y", "scarica immagine"],
			], [
				"video.player",
				["U/O", "salta 10sec indietro/avanti"],
				["P/K/Spazio", "play/pausa"],
				["C", "continua riproduzione successivo"],
				["V", "loop"],
				["M", "muto"],
				["[ e ]", "imposta intervallo loop"],
			], [
				"textfile-viewer",
				["I/K", "file prec/succ"],
				["M", "chiudi file di testo"],
				["E", "modifica file di testo"],
				["S", "seleziona file (per taglia/copia/rinomina)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Annulla",

		"enable": "Abilita",
		"danger": "PERICOLO",
		"clipped": "copiato negli appunti",

		"ht_s1": "secondo",
		"ht_s2": "secondi",
		"ht_m1": "minuto",
		"ht_m2": "minuti",
		"ht_h1": "ora",
		"ht_h2": "ore",
		"ht_d1": "giorno",
		"ht_d2": "giorni",
		"ht_and": " e ",

		"goh": "control-panel",
		"gop": 'cartella sorella precedente">prec',
		"gou": 'cartella genitore">su',
		"gon": 'prossima cartella">succ',
		"logout": "Logout ",
		"login": "Accedi", //m
		"access": " accesso",
		"ot_close": "chiudi sottomenu",
		"ot_search": "cerca file per attributi, percorso / nome, tag musicali, o qualsiasi combinazione di questi$N$N&lt;code&gt;foo bar&lt;/code&gt; = deve contenere sia «foo» che «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = deve contenere «foo» ma non «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = inizia con «yana» ed è un file «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = contiene esattamente «try unite»$N$Nil formato data è iso-8601, come$N&lt;code&gt;2009-12-31&lt;/code&gt; o &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: elimina i tuoi caricamenti recenti, o interrompi quelli non completati",
		"ot_bup": "bup: uploader di base, supporta anche netscape 4.0",
		"ot_mkdir": "mkdir: crea una nuova directory",
		"ot_md": "new-md: crea un nuovo documento markdown",
		"ot_msg": "msg: invia un messaggio al log del server",
		"ot_mp": "opzioni lettore multimediale",
		"ot_cfg": "opzioni di configurazione",
		"ot_u2i": 'up2k: carica file (se hai accesso in scrittura) o attiva la modalità ricerca per vedere se esistono già da qualche parte sul server$N$NI caricamenti sono ripristinabili, multithreaded, e i timestamp dei file vengono preservati, ma usa più CPU di [🎈]&nbsp; (l\'uploader di base)<br /><br />durante i caricamenti, questa icona diventa un indicatore di progresso!',
		"ot_u2w": 'up2k: carica file con supporto per il ripristino (chiudi il browser e trascina gli stessi file più tardi)$N$NMultithreaded, e i timestamp dei file vengono preservati, ma usa più CPU di [🎈]&nbsp; (l\'uploader di base)<br /><br />durante i caricamenti, questa icona diventa un indicatore di progresso!',
		"ot_noie": 'Perfavore usa Chrome / Firefox / Edge',

		"ab_mkdir": "crea directory",
		"ab_mkdoc": "nuovo doc markdown",
		"ab_msg": "invia msg al log srv",

		"ay_path": "salta alle cartelle",
		"ay_files": "salta ai file",

		"wt_ren": "rinomina elementi selezionati$NTasto rapido: F2",
		"wt_del": "elimina elementi selezionati$NTasto rapido: ctrl-K",
		"wt_cut": "taglia elementi selezionati &lt;small&gt;(poi incolla altrove)&lt;/small&gt;$NTasto rapido: ctrl-X",
		"wt_cpy": "copia elementi selezionati negli appunti$N(per incollarli altrove)$NTasto rapido: ctrl-C",
		"wt_pst": "incolla una selezione precedentemente tagliata / copiata$NTasto rapido: ctrl-V",
		"wt_selall": "seleziona tutti i file$NTasto rapido: ctrl-A (quando il file è focalizzato)",
		"wt_selinv": "inverti selezione",
		"wt_zip1": "scarica questa cartella come archivio",
		"wt_selzip": "scarica selezione come archivio",
		"wt_seldl": "scarica selezione come file separati$NTasto rapido: Y",
		"wt_npirc": "copia info traccia formato irc",
		"wt_nptxt": "copia info traccia testo semplice",
		"wt_m3ua": "aggiungi alla playlist m3u (clicca <code>📻copia</code> dopo)",
		"wt_m3uc": "copia playlist m3u negli appunti",
		"wt_grid": "alterna vista griglia / lista$NTasto rapido: G",
		"wt_prev": "traccia precedente$NTasto rapido: J",
		"wt_play": "play / pausa$NTasto rapido: P",
		"wt_next": "traccia successiva$NTasto rapido: L",

		"ul_par": "caricamenti paralleli:",
		"ut_rand": "randomizza nomi file",
		"ut_u2ts": "copia il timestamp di ultima modifica$Ndal tuo filesystem al server\">📅",
		"ut_ow": "sovrascrivere file esistenti sul server?$N🛡️: mai (genererà un nuovo nome file)$N🕒: sovrascrivi se il file del server è più vecchio del tuo$N♻️: sovrascrivi sempre se i file sono diversi",
		"ut_mt": "continua l'hashing di altri file durante il caricamento$N$NProva a disabilitare se la tua CPU o HDD è un collo di bottiglia",
		"ut_ask": 'chiedi conferma prima che inizi il caricamento">💭',
		"ut_pot": "migliora la velocità di caricamento su dispositivi lenti$Nrendendo l'interfaccia meno complessa",
		"ut_srch": "non caricare realmente, invece controlla se i file esistono già $N sul server (scansionerà tutte le cartelle che puoi leggere)",
		"ut_par": "metti in pausa i caricamenti impostandolo a 0$N$NAumenta se la tua connessione è lenta / alta latenza$N$NMantienilo a 1 su LAN o se l'HDD del server è un collo di bottiglia",
		"ul_btn": "trascina file / cartelle<br>qui (o cliccami)",
		"ul_btnu": "C A R I C A",
		"ul_btns": "C E R C A",

		"ul_hash": "hash",
		"ul_send": "invia",
		"ul_done": "fatto",
		"ul_idle1": "nessun caricamento ancora in coda",
		"ut_etah": "velocità media di &lt;em&gt;hashing&lt;/em&gt;, e tempo stimato al completamento",
		"ut_etau": "velocità media di &lt;em&gt;caricamento&lt;/em&gt; e tempo stimato al completamento",
		"ut_etat": "velocità &lt;em&gt;totale&lt;/em&gt; media e tempo stimato al completamento",

		"uct_ok": "completato con successo",
		"uct_ng": "non-valido: fallito / rifiutato / non-trovato",
		"uct_done": "ok e ng combinati",
		"uct_bz": "hashing o caricamento",
		"uct_q": "inattivo, in attesa",

		"utl_name": "nome file",
		"utl_ulist": "lista",
		"utl_ucopy": "copia",
		"utl_links": "link",
		"utl_stat": "stato",
		"utl_prog": "progresso",

		// keep short:
		"utl_404": "404",
		"utl_err": "ERRORE",
		"utl_oserr": "Errore-SO",
		"utl_found": "trovato",
		"utl_defer": "rinvia",
		"utl_yolo": "YOLO",
		"utl_done": "finito",

		"ul_flagblk": "i file sono stati aggiunti alla coda</b><br>tuttavia c'è un up2k occupato in un'altra scheda del browser,<br>quindi aspetto che quello finisca prima",
		"ul_btnlk": "la configurazione del server ha bloccato questo interruttore in questo stato",

		"udt_up": "Carica",
		"udt_srch": "Cerca",
		"udt_drop": "lascialo qui",

		"u_nav_m": '<h6>ok, cosa hai?</h6><code>Invio</code> = File (uno o più)\n<code>ESC</code> = Una cartella (incluse sottocartelle)',
		"u_nav_b": '<a href="#" id="modal-ok">File</a><a href="#" id="modal-ng">Una cartella</a>',

		"cl_opts": "opzioni",
		"cl_themes": "tema",
		"cl_langs": "lingua",
		"cl_ziptype": "download cartella",
		"cl_uopts": "opzioni up2k",
		"cl_favico": "favicon",
		"cl_bigdir": "cartelle grandi",
		"cl_hsort": "#ordinamento",
		"cl_keytype": "notazione tasti",
		"cl_hiddenc": "colonne nascoste",
		"cl_hidec": "nascondi",
		"cl_reset": "reset",
		"cl_hpick": "tocca le intestazioni delle colonne per nascondere nella tabella sottostante",
		"cl_hcancel": "nascondere colonne annullato",

		"ct_grid": '田 griglia',
		"ct_ttips": '◔ ◡ ◔">ℹ️ tooltip',
		"ct_thumb": 'nella vista griglia, alterna icone o miniature$NTasto rapido: T">🖼️ miniature',
		"ct_csel": 'usa CTRL e SHIFT per la selezione file nella vista griglia">sel',
		"ct_ihop": 'quando il visualizzatore immagini è chiuso, scorri fino all\'ultimo file visualizzato">g⮯',
		"ct_dots": 'mostra file nascosti (se il server lo permette)">dotfile',
		"ct_qdel": 'quando elimini file, chiedi conferma solo una volta">qdel',
		"ct_dir1st": 'ordina cartelle prima dei file">📁 prima',
		"ct_nsort": 'ordinamento naturale (per nomi file con cifre iniziali)">nsort',
		"ct_utc": 'mostra tutte le date/ore in UTC">UTC',
		"ct_readme": 'mostra README.md negli elenchi cartelle">📜 readme',
		"ct_idxh": 'mostra index.html invece dell\'elenco cartelle">htm',
		"ct_sbars": 'mostra barre di scorrimento">⟊',

		"cut_umod": "se un file esiste già sul server, aggiorna il timestamp di ultima modifica del server per farlo coincidere con il tuo file locale (richiede permessi di scrittura+eliminazione)\">re📅",

		"cut_turbo": "il pulsante yolo, probabilmente NON lo vuoi abilitare:$N$NUsalo se stavi caricando una grande quantità di file e hai dovuto riavviare per qualche motivo, e vuoi continuare il caricamento il prima possibile$N$NQuesto sostituisce il controllo hash con un semplice <em>&quot;questo ha la stessa dimensione file sul server?&quot;</em> quindi se il contenuto del file è diverso NON verrà caricato$N$NDovresti spegnere questo quando il caricamento è finito, e poi &quot;caricare&quot; di nuovo gli stessi file per far verificare al client\">turbo",

		"cut_datechk": "non ha effetto a meno che il pulsante turbo sia abilitato$N$NRiduce il fattore yolo di una piccola quantità; controlla se i timestamp dei file sul server corrispondono ai tuoi$N$NDovrebbe <em>teoricamente</em> catturare la maggior parte dei caricamenti non finiti / corrotti, ma non è un sostituto per fare un passaggio di verifica con turbo disabilitato dopo\">date-chk",

		"cut_u2sz": "dimensione (in MiB) di ogni chunk di caricamento; valori grandi volano meglio attraverso l'atlantico. Prova valori bassi su connessioni molto inaffidabili",

		"cut_flag": "assicura che solo una scheda stia caricando alla volta $N -- anche le altre schede devono avere questo abilitato $N -- influisce solo sulle schede dello stesso dominio",

		"cut_az": "carica file in ordine alfabetico, invece che dal file più piccolo prima$N$NL'ordine alfabetico può rendere più facile controllare a occhio se qualcosa è andato storto sul server, ma rende il caricamento leggermente più lento su fibra / LAN",

		"cut_nag": "notifica SO quando il caricamento si completa$N(solo se il browser o la scheda non è attiva)",
		"cut_sfx": "allarme sonoro quando il caricamento si completa$N(solo se il browser o la scheda non è attiva)",

		"cut_mt": "usa multithreading per accelerare l'hashing dei file$N$NQuesto usa web-worker e richiede$Npiù RAM (fino a 512 MiB extra)$N$NRende https 30% più veloce, http 4.5x più veloce\">mt",

		"cut_wasm": "usa wasm invece dell'hasher integrato del browser; migliora la velocità sui browser basati su chrome ma aumenta il carico CPU, e molte versioni vecchie di chrome hanno bug che fanno consumare tutta la RAM al browser e crashare se questo è abilitato\">wasm",

		"cft_text": "testo favicon (vuoto e aggiorna per disabilitare)",
		"cft_fg": "colore primo piano",
		"cft_bg": "colore sfondo",

		"cdt_lim": "numero massimo di file da mostrare in una cartella",
		"cdt_ask": "quando scorri verso il fondo,$Ninvece di caricare più file,$Nchiedi cosa fare",
		"cdt_hsort": "quante regole di ordinamento (&lt;code&gt;,sorthref&lt;/code&gt;) includere negli URL multimediali. Impostandolo a 0 ignorerà anche le regole di ordinamento incluse nei link multimediali quando li clicchi",

		"tt_entree": "mostra pannello nav (barra laterale albero directory)$NTasto rapido: B",
		"tt_detree": "mostra breadcrumb$NTasto rapido: B",
		"tt_visdir": "scorri alla cartella selezionata",
		"tt_ftree": "alterna albero cartelle / file di testo$NTasto rapido: V",
		"tt_pdock": "mostra cartelle genitore in un pannello ancorato in alto",
		"tt_dynt": "crescita automatica mentre l'albero si espande",
		"tt_wrap": "a capo parola",
		"tt_hover": "rivela righe che traboccano al passaggio del mouse$N( interrompe lo scorrimento a meno che il cursore $N&nbsp; del mouse non sia nella grondaia sinistra )",

		"ml_pmode": "alla fine della cartella...",
		"ml_btns": "comandi",
		"ml_tcode": "transcodifica",
		"ml_tcode2": "transcodifica in",
		"ml_tint": "tinta",
		"ml_eq": "equalizzatore audio",
		"ml_drc": "compressore gamma dinamica",

		"mt_loop": "loop/ripeti una canzone\">🔁",
		"mt_one": "fermati dopo una canzone\">1️⃣",
		"mt_shuf": "mescola le canzoni in ogni cartella\">🔀",
		"mt_aplay": "autoplay se c'è un song-ID nel link che hai cliccato per accedere al server$N$NDisabilitando questo fermerà anche l'aggiornamento dell'URL della pagina con song-ID quando riproduci musica, per prevenire autoplay se queste impostazioni vengono perse ma l'URL rimane\">a▶",
		"mt_preload": "inizia a caricare la prossima canzone verso la fine per riproduzione senza interruzioni\">preload",
		"mt_prescan": "vai alla prossima cartella prima che finisca l'ultima canzone$Nmantenendo felice il browser web$Ncosì non si ferma la riproduzione\">nav",
		"mt_fullpre": "prova a precaricare l'intera canzone;$N✅ abilita su connessioni <b>inaffidabili</b>,$N❌ <b>disabilita</b> su connessioni lente probabilmente\">full",
		"mt_fau": "sui telefoni, previeni che la musica si fermi se la prossima canzone non si precarica abbastanza velocemente (può rendere glitchy la visualizzazione dei tag)\">☕️",
		"mt_waves": "barra di ricerca forma d'onda:$Nmostra ampiezza audio nello scrubber\">~s",
		"mt_npclip": "mostra pulsanti per copiare negli appunti la canzone attualmente in riproduzione\">/np",
		"mt_m3u_c": "mostra pulsanti per copiare negli appunti le$Ncanzoni selezionate come voci playlist m3u8\">📻",
		"mt_octl": "integrazione so (tasti multimediali / osd)\">os-ctl",
		"mt_oseek": "permetti ricerca attraverso integrazione so$N$Nnota: su alcuni dispositivi (iPhone),$Nquesto sostituisce il pulsante canzone successiva\">seek",
		"mt_oscv": "mostra copertina album in osd\">art",
		"mt_follow": "mantieni la traccia in riproduzione scorrevole nella vista\">🎯",
		"mt_compact": "controlli compatti\">⟎",
		"mt_uncache": "pulisci cache &nbsp;(prova ad attivare se il tuo browser ha messo in cache$Nuna copia rotta di una canzone e si rifiuta di riprodurla)\">uncache",
		"mt_mloop": "loop della cartella aperta\">🔁 loop",
		"mt_mnext": "carica la prossima cartella e continua\">📂 succ",
		"mt_mstop": "ferma riproduzione\">⏸ stop",
		"mt_cflac": "converti flac / wav in {0}\">flac",
		"mt_caac": "converti aac / m4a in {0}\">aac",
		"mt_coth": "converti tutti gli altri (non mp3) in {0}\">oth",
		"mt_c2opus": "scelta migliore per desktop, laptop, android\">opus",
		"mt_c2owa": "opus-weba, per iOS 17.5 e più recenti\">owa",
		"mt_c2caf": "opus-caf, per iOS 11 fino a 17\">caf",
		"mt_c2mp3": "usa questo su dispositivi molto vecchi\">mp3",
		"mt_c2flac": "qualità audio migliore, ma download pesanti\">flac", //m
		"mt_c2wav": "riproduzione non compressa (ancora più grande)\">wav", //m
		"mt_c2ok": "bene, buona scelta",
		"mt_c2nd": "quello non è il formato di output raccomandato per il tuo dispositivo, ma va bene",
		"mt_c2ng": "il tuo dispositivo non sembra supportare questo formato di output, ma proviamo comunque",
		"mt_xowa": "ci sono bug in iOS che prevengono la riproduzione in background usando questo formato; usa caf o mp3 invece",
		"mt_tint": "livello sfondo (0-100) sulla barra di ricerca$Nper rendere il buffering meno distraente",
		"mt_eq": "abilita l'equalizzatore e controllo guadagno;$N$Nboost &lt;code&gt;0&lt;/code&gt; = volume standard 100% (non modificato)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = stereo standard (non modificato)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% crossfeed sinistra-destra$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = rimozione vocale :^)$N$Nabilitando l'equalizzatore rende gli album senza interruzioni completamente senza interruzioni, quindi lascialo acceso con tutti i valori a zero (eccetto width = 1) se ti importa di quello",
		"mt_drc": "abilita il compressore gamma dinamica (appiattitore volume / brickwaller); abiliterà anche EQ per bilanciare gli spaghetti, quindi imposta tutti i campi EQ eccetto 'width' a 0 se non lo vuoi$N$NAbbassa il volume dell'audio sopra THRESHOLD dB; per ogni RATIO dB oltre THRESHOLD c'è 1 dB di output, quindi i valori di default di tresh -24 e ratio 12 significa che non dovrebbe mai diventare più forte di -22 dB ed è sicuro aumentare il boost equalizzatore a 0.8, o anche 1.8 con ATK 0 e un RLS enorme come 90 (funziona solo in firefox; RLS è max 1 in altri browser)$N$N(vedi wikipedia, lo spiegano molto meglio)",

		"mb_play": "riproduci",
		"mm_hashplay": "riprodurre questo file audio?",
		"mm_m3u": "premi <code>Invio/OK</code> per Riprodurre\npremi <code>ESC/Annulla</code> per Modificare",
		"mp_breq": "serve firefox 82+ o chrome 73+ o iOS 15+",
		"mm_bload": "ora caricando...",
		"mm_bconv": "convertendo in {0}, attendi...",
		"mm_opusen": "il tuo browser non può riprodurre file aac / m4a;\ntranscodifica in opus ora abilitata",
		"mm_playerr": "riproduzione fallita: ",
		"mm_eabrt": "Il tentativo di riproduzione è stato cancellato",
		"mm_enet": "La tua connessione internet è instabile",
		"mm_edec": "Questo file è presumibilmente corrotto??",
		"mm_esupp": "Il tuo browser non capisce questo formato audio",
		"mm_eunk": "Errore Sconosciuto",
		"mm_e404": "Non è stato possibile riprodurre audio; errore 404: File non trovato.",
		"mm_e403": "Non è stato possibile riprodurre audio; errore 403: Accesso negato.\n\nProva a premere F5 per ricaricare, forse sei stato disconnesso",
		"mm_e500": "Non è stato possibile riprodurre audio; errore 500: Controlla i log del server.",
		"mm_e5xx": "Non è stato possibile riprodurre audio; errore server ",
		"mm_nof": "non trovo altri file audio nelle vicinanze",
		"mm_prescan": "Cercando musica da riprodurre dopo...",
		"mm_scank": "Trovata la prossima canzone:",
		"mm_uncache": "cache pulita; tutte le canzoni si riscaricheranno alla prossima riproduzione",
		"mm_hnf": "quella canzone non esiste più",

		"im_hnf": "quell'immagine non esiste più",

		"f_empty": 'questa cartella è vuota',
		"f_chide": 'questo nasconderà la colonna «{0}»\n\npuoi mostrare le colonne nella scheda impostazioni',
		"f_bigtxt": "questo file è {0} MiB grande -- visualizzare davvero come testo?",
		"f_bigtxt2": "visualizzare solo la fine del file invece? questo abiliterà anche following/tailing, mostrando righe di testo appena aggiunte in tempo reale",
		"fbd_more": '<div id="blazy">mostrando <code>{0}</code> di <code>{1}</code> file; <a href="#" id="bd_more">mostra {2}</a> o <a href="#" id="bd_all">mostra tutti</a></div>',
		"fbd_all": '<div id="blazy">mostrando <code>{0}</code> di <code>{1}</code> file; <a href="#" id="bd_all">mostra tutti</a></div>',
		"f_anota": "solo {0} dei {1} elementi sono stati selezionati;\nper selezionare l'intera cartella, prima scorri fino in fondo",

		"f_dls": 'i link dei file nella cartella corrente sono stati\ncambiati in link di download',

		"f_partial": "Per scaricare in sicurezza un file che è attualmente in fase di caricamento, clicca il file che ha lo stesso nome, ma senza l'estensione <code>.PARTIAL</code>. Premi ANNULLA o Escape per farlo.\n\nPremendo OK / Invio ignorerai questo avviso e continuerai a scaricare il file <code>.PARTIAL</code> scratch, che quasi sicuramente ti darà dati corrotti.",

		"ft_paste": "incolla {0} elementi$NTasto rapido: ctrl-V",
		"fr_eperm": 'impossibile rinominare:\nnon hai il permesso “sposta” in questa cartella',
		"fd_eperm": 'impossibile eliminare:\nnon hai il permesso “elimina” in questa cartella',
		"fc_eperm": 'impossibile tagliare:\nnon hai il permesso “sposta” in questa cartella',
		"fp_eperm": 'impossibile incollare:\nnon hai il permesso “scrivi” in questa cartella',
		"fr_emore": "seleziona almeno un elemento da rinominare",
		"fd_emore": "seleziona almeno un elemento da eliminare",
		"fc_emore": "seleziona almeno un elemento da tagliare",
		"fcp_emore": "seleziona almeno un elemento da copiare negli appunti",

		"fs_sc": "condividi la cartella in cui ti trovi",
		"fs_ss": "condividi i file selezionati",
		"fs_just1d": "non puoi selezionare più di una cartella,\no mescolare file e cartelle in una selezione",
		"fs_abrt": "❌ interrompi",
		"fs_rand": "🎲 nome.casuale",
		"fs_go": "✅ crea condivisione",
		"fs_name": "nome",
		"fs_src": "sorgente",
		"fs_pwd": "password",
		"fs_exp": "scadenza",
		"fs_tmin": "min",
		"fs_thrs": "ore",
		"fs_tdays": "giorni",
		"fs_never": "eterno",
		"fs_pname": "nome link opzionale; sarà casuale se vuoto",
		"fs_tsrc": "il file o cartella da condividere",
		"fs_ppwd": "password opzionale",
		"fs_w8": "creando condivisione...",
		"fs_ok": "premi <code>Invio/OK</code> per Appunti\npremi <code>ESC/Annulla</code> per Chiudere",

		"frt_dec": "può risolvere alcuni casi di nomi file corrotti\">url-decode",
		"frt_rst": "ripristina nomi file modificati a quelli originali\">↺ reset",
		"frt_abrt": "interrompi e chiudi questa finestra\">❌ annulla",
		"frb_apply": "APPLICA RINOMINA",
		"fr_adv": "rinomina batch / metadata / pattern\">avanzato",
		"fr_case": "regex case-sensitive\">maiusc",
		"fr_win": "nomi sicuri per windows; sostituisce <code>&lt;&gt;:&quot;\\|?*</code> con caratteri giapponesi fullwidth\">win",
		"fr_slash": "sostituisce <code>/</code> con un carattere che non causa la creazione di nuove cartelle\">no /",
		"fr_re": "pattern di ricerca regex da applicare ai nomi file originali; i gruppi di cattura possono essere referenziati nel campo formato sottostante come &lt;code&gt;(1)&lt;/code&gt; e &lt;code&gt;(2)&lt;/code&gt; e così via",
		"fr_fmt": "ispirato da foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; è sostituito dal titolo della canzone,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; salta [questa] parte se artista è vuoto$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; aggiunge padding al numero traccia a 2 cifre",
		"fr_pdel": "elimina",
		"fr_pnew": "salva come",
		"fr_pname": "fornisci un nome per il tuo nuovo preset",
		"fr_aborted": "interrotto",
		"fr_lold": "nome vecchio",
		"fr_lnew": "nome nuovo",
		"fr_tags": "tag per i file selezionati (sola lettura, solo per riferimento):",
		"fr_busy": "rinominando {0} elementi...\n\n{1}",
		"fr_efail": "rinomina fallita:\n",
		"fr_nchg": "{0} dei nuovi nomi sono stati alterati a causa di <code>win</code> e/o <code>no /</code>\n\nOK per continuare con questi nuovi nomi alterati?",

		"fd_ok": "eliminazione OK",
		"fd_err": "eliminazione fallita:\n",
		"fd_none": "niente è stato eliminato; forse bloccato dalla configurazione server (xbd)?",
		"fd_busy": "eliminando {0} elementi...\n\n{1}",
		"fd_warn1": "ELIMINARE questi {0} elementi?",
		"fd_warn2": "<b>Ultima possibilità!</b> Nessun modo per annullare. Eliminare?",

		"fc_ok": "tagliati {0} elementi",
		"fc_warn": 'tagliati {0} elementi\n\nma: solo <b>questa</b> scheda-browser può incollarli\n(dato che la selezione è così assolutamente massiva)',

		"fcc_ok": "copiati {0} elementi negli appunti",
		"fcc_warn": 'copiati {0} elementi negli appunti\n\nma: solo <b>questa</b> scheda-browser può incollarli\n(dato che la selezione è così assolutamente massiva)',

		"fp_apply": "usa questi nomi",
		"fp_ecut": "prima taglia o copia alcuni file / cartelle da incollare / spostare\n\nnota: puoi tagliare / incollare attraverso diverse schede del browser",
		"fp_ename": "{0} elementi non possono essere spostati qui perché i nomi sono già presi. Dai loro nuovi nomi qui sotto per continuare, o lascia vuoto il nome per saltarli:",
		"fcp_ename": "{0} elementi non possono essere copiati qui perché i nomi sono già presi. Dai loro nuovi nomi qui sotto per continuare, o lascia vuoto il nome per saltarli:",
		"fp_emore": "ci sono ancora alcune collisioni di nomi file rimaste da risolvere",
		"fp_ok": "spostamento OK",
		"fcp_ok": "copia OK",
		"fp_busy": "spostando {0} elementi...\n\n{1}",
		"fcp_busy": "copiando {0} elementi...\n\n{1}",
		"fp_abrt": "annullamento in corso...", //m
		"fp_err": "spostamento fallito:\n",
		"fcp_err": "copia fallita:\n",
		"fp_confirm": "spostare questi {0} elementi qui?",
		"fcp_confirm": "copiare questi {0} elementi qui?",
		"fp_etab": 'fallito leggere appunti da altra scheda browser',
		"fp_name": "caricando un file dal tuo dispositivo. Dagli un nome:",
		"fp_both_m": '<h6>scegli cosa incollare</h6><code>Invio</code> = Sposta {0} file da «{1}»\n<code>ESC</code> = Carica {2} file dal tuo dispositivo',
		"fcp_both_m": '<h6>scegli cosa incollare</h6><code>Invio</code> = Copia {0} file da «{1}»\n<code>ESC</code> = Carica {2} file dal tuo dispositivo',
		"fp_both_b": '<a href="#" id="modal-ok">Sposta</a><a href="#" id="modal-ng">Carica</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Copia</a><a href="#" id="modal-ng">Carica</a>',

		"mk_noname": "scrivi un nome nel campo di testo a sinistra prima di farlo :p",

		"tv_load": "Caricando documento di testo:\n\n{0}\n\n{1}% ({2} di {3} MiB caricati)",
		"tv_xe1": "impossibile caricare file di testo:\n\nerrore ",
		"tv_xe2": "404, file non trovato",
		"tv_lst": "lista di file di testo in",
		"tvt_close": "torna alla vista cartella$NTasto rapido: M (o Esc)\">❌ chiudi",
		"tvt_dl": "scarica questo file$NTasto rapido: Y\">💾 scarica",
		"tvt_prev": "mostra documento precedente$NTasto rapido: i\">⬆ prec",
		"tvt_next": "mostra documento successivo$NTasto rapido: K\">⬇ succ",
		"tvt_sel": "seleziona file &nbsp; ( per taglia / copia / elimina / ... )$NTasto rapido: S\">sel",
		"tvt_edit": "apri file nell'editor di testo$NTasto rapido: E\">✏️ modifica",
		"tvt_tail": "monitora file per cambiamenti; mostra nuove righe in tempo reale\">📡 segui",
		"tvt_wrap": "a capo parola\">↵",
		"tvt_atail": "blocca scorrimento in fondo alla pagina\">⚓",
		"tvt_ctail": "decodifica colori terminale (codici escape ansi)\">🌈",
		"tvt_ntail": "limite scrollback (quanti byte di testo mantenere caricati)",

		"m3u_add1": "canzone aggiunta alla playlist m3u",
		"m3u_addn": "{0} canzoni aggiunte alla playlist m3u",
		"m3u_clip": "playlist m3u ora copiata negli appunti\n\ndovresti creare un nuovo file di testo chiamato qualcosa.m3u e incollare la playlist in quel documento; questo la renderà riproducibile",

		"gt_vau": "non mostrare video, riproduci solo l'audio\">🎧",
		"gt_msel": "abilita selezione file; ctrl-click un file per sovrascrivere$N$N&lt;em&gt;quando attivo: doppio-click un file / cartella per aprirlo&lt;/em&gt;$N$NTasto rapido: S\">multiselezione",
		"gt_crop": "ritaglia miniature al centro\">ritaglia",
		"gt_3x": "miniature hi-res\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "taglia",
		"gt_sort": "ordina per",
		"gt_name": "nome",
		"gt_sz": "dimensione",
		"gt_ts": "data",
		"gt_ext": "tipo",
		"gt_c1": "tronca nomi file di più (mostra meno)",
		"gt_c2": "tronca nomi file di meno (mostra di più)",

		"sm_w8": "cercando...",
		"sm_prev": "i risultati di ricerca qui sotto sono da una query precedente:\n  ",
		"sl_close": "chiudi risultati ricerca",
		"sl_hits": "mostrando {0} risultati",
		"sl_moar": "carica altro",

		"s_sz": "dimensione",
		"s_dt": "data",
		"s_rd": "percorso",
		"s_fn": "nome",
		"s_ta": "tag",
		"s_ua": "car@",
		"s_ad": "avanz.",
		"s_s1": "MiB minimo",
		"s_s2": "MiB massimo",
		"s_d1": "iso8601 min.",
		"s_d2": "iso8601 max.",
		"s_u1": "caricato dopo",
		"s_u2": "e/o prima",
		"s_r1": "percorso contiene &nbsp; (separato da spazi)",
		"s_f1": "nome contiene &nbsp; (nega con -nope)",
		"s_t1": "tag contiene &nbsp; (^=inizio, fine=$)",
		"s_a1": "proprietà metadata specifiche",

		"md_eshow": "impossibile renderizzare ",
		"md_off": "[📜<em>readme</em>] disabilitato in [⚙️] -- documento nascosto",

		"badreply": "Fallito nel parsare risposta dal server",

		"xhr403": "403: Accesso negato\n\nprova a premere F5, forse sei stato disconnesso",
		"xhr0": "sconosciuto (probabilmente persa connessione al server, o server offline)",
		"cf_ok": "scusa per quello -- la protezione DD" + wah + "oS è entrata in azione\n\nle cose dovrebbero riprendere in circa 30 sec\n\nse non succede niente, premi F5 per ricaricare la pagina",
		"tl_xe1": "impossibile elencare sottocartelle:\n\nerrore ",
		"tl_xe2": "404: Cartella non trovata",
		"fl_xe1": "impossibile elencare file nella cartella:\n\nerrore ",
		"fl_xe2": "404: Cartella non trovata",
		"fd_xe1": "impossibile creare sottocartella:\n\nerrore ",
		"fd_xe2": "404: Cartella genitore non trovata",
		"fsm_xe1": "impossibile inviare messaggio:\n\nerrore ",
		"fsm_xe2": "404: Cartella genitore non trovata",
		"fu_xe1": "fcaricamento fallito per la lista unpost dal server:\n\nerrore ",
		"fu_xe2": "404: File non trovato??",

		"fz_tar": "file gnu-tar non compresso (linux / mac)",
		"fz_pax": "tar formato pax non compresso (più lento)",
		"fz_targz": "gnu-tar con compressione gzip livello 3$N$NSolitamente è molto lento, quindi$Nusa tar non compresso",
		"fz_tarxz": "gnu-tar con compressione xz livello 1$N$NQuesto è solitamente molto lento, quindi$Nusa tar non compresso",
		"fz_zip8": "zip con nomi file utf8 (forse instabile su windows 7 e precedenti)",
		"fz_zipd": "zip con nomi file cp437 tradizionali, per software molto vecchio",
		"fz_zipc": "cp437 con crc32 calcolato presto,$Nper MS-DOS PKZIP v2.04g (ottobre 1993)$N(ci vuole più tempo per elaborare prima che possa iniziare il download)",

		"un_m1": "puoi eliminare i tuoi caricamenti recenti (o interrompere quelli non finiti) qui sotto",
		"un_upd": "aggiorna",
		"un_m4": "o condividi i file visibili qui sotto:",
		"un_ulist": "mostra",
		"un_ucopy": "copia",
		"un_flt": "filtro opzionale:&nbsp; URL deve contenere",
		"un_fclr": "resetta filtro",
		"un_derr": 'unpost-delete fallito:\n',
		"un_f5": 'qualcosa si è rotto, prova un aggiornamento o premi F5',
		"un_uf5": "scusa ma devi aggiornare la pagina (per esempio premendo F5 o CTRL-R) prima che questo caricamento possa essere interrotto",
		"un_nou": '<b>avviso:</b> server troppo occupato per mostrare caricamenti non finiti; clicca il link "aggiorna" tra un po\'',
		"un_noc": '<b>avviso:</b> unpost di file completamente caricati non è abilitato/permesso nella configurazione server',
		"un_max": "mostrando primi 2000 file (usa il filtro)",
		"un_avail": "{0} caricamenti recenti possono essere eliminati<br />{1} non finiti possono essere interrotti",
		"un_m2": "ordinati per tempo di caricamento; più recenti prima:",
		"un_no1": "scherzo! nessun caricamento è abbastanza recente",
		"un_no2": "scherzo! nessun caricamento che corrisponde a quel filtro è abbastanza recente",
		"un_next": "elimina i prossimi {0} file qui sotto",
		"un_abrt": "interrompi",
		"un_del": "elimina",
		"un_m3": "caricando i tuoi caricamenti recenti...",
		"un_busy": "eliminando {0} file...",
		"un_clip": "{0} link copiati negli appunti",

		"u_https1": "dovresti",
		"u_https2": "passare a https",
		"u_https3": "per prestazioni migliori",
		"u_ancient": 'il tuo browser è incredibilmente antico -- forse dovresti <a href="#" onclick="goto(\'bup\')">usare bup invece</a>',
		"u_nowork": "serve firefox 53+ o chrome 57+ o iOS 11+",
		"tail_2old": "serve firefox 105+ o chrome 71+ o iOS 14.5+",
		"u_nodrop": 'il tuo browser è troppo vecchio per il caricamento drag-and-drop',
		"u_notdir": "quella non è una cartella!\n\nil tuo browser è troppo vecchio,\nprova dragdrop invece",
		"u_uri": "per trascinare immagini da altre finestre del browser,\nrilasciale sul pulsante upload grande",
		"u_enpot": 'passa alla <a href="#">UI patata</a> (può migliorare velocità upload)',
		"u_depot": 'passa alla <a href="#">UI elegante</a> (può ridurre velocità upload)',
		"u_gotpot": 'passando alla UI patata per migliorare velocità upload,\n\nsentiti libero di non essere d\'accordo e tornare indietro!',
		"u_pott": "<p>file: &nbsp; <b>{0}</b> finiti, &nbsp; <b>{1}</b> falliti, &nbsp; <b>{2}</b> occupati, &nbsp; <b>{3}</b> in coda</p>",
		"u_ever": "questo è l'uploader di base; up2k necessita almeno<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'questo è l\'uploader di base; <a href="#" id="u2yea">up2k</a> è migliore',
		"u_uput": 'velocizza (salta checksum)',
		"u_ewrite": 'non hai accesso in scrittura a questa cartella',
		"u_eread": 'non hai accesso in lettura a questa cartella',
		"u_enoi": 'file-search non è abilitato nella configurazione server',
		"u_enoow": "non puoi sovrascrivere qui; serve permesso Elimina",
		"u_badf": 'Questi {0} file (di {1} totali) sono stati saltati, probabilmente a causa di permessi filesystem:\n\n',
		"u_blankf": 'Questi {0} file (di {1} totali) sono vuoti; caricarli comunque?\n\n',
		"u_applef": 'Questi {0} file (di {1} totali) sono probabilmente indesiderabili;\nPremi <code>OK/Invio</code> per SALTARE i seguenti file,\nPremi <code>Annulla/ESC</code> per NON escludere, e CARICARE anche quelli:\n\n',
		"u_just1": '\nForse funziona meglio se selezioni solo un file',
		"u_ff_many": "se stai usando <b>Linux / MacOS / Android,</b> allora questa quantità di file <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>potrebbe</em> far crashare Firefox!</a>\nse succede, riprova (o usa Chrome).",
		"u_up_life": "Questo caricamento sarà eliminato dal server\n{0} dopo che si completa",
		"u_asku": 'caricare questi {0} file in <code>{1}</code>',
		"u_unpt": "puoi annullare / eliminare questo caricamento usando 🧯 in alto a sinistra",
		"u_bigtab": 'sto per mostrare {0} file\n\nquesto potrebbe far crashare il tuo browser, sei sicuro?',
		"u_scan": 'Scansionando file...',
		"u_dirstuck": 'iteratore directory si è bloccato tentando di accedere ai seguenti {0} elementi; salterò:',
		"u_etadone": 'Fatto ({0}, {1} file)',
		"u_etaprep": '(preparando per caricare)',
		"u_hashdone": 'hashing completato',
		"u_hashing": 'hash',
		"u_hs": 'handshaking...',
		"u_started": "i file ora sono in caricamento; vedi [🚀]",
		"u_dupdefer": "duplicato; sarà processato dopo tutti gli altri file",
		"u_actx": "clicca questo testo per prevenire perdita di<br />prestazioni quando cambi ad altre finestre/schede",
		"u_fixed": "OK!&nbsp; Risolto 👍",
		"u_cuerr": "caricamento fallito del chunk {0} di {1};\nprobabilmente innocuo, continuo\n\nfile: {2}",
		"u_cuerr2": "il server ha rifiutato il caricamento (chunk {0} di {1});\nriproverò più tardi\n\nfile: {2}\n\nerrore ",
		"u_ehstmp": "riproverò; vedi in basso a destra",
		"u_ehsfin": "il server ha rifiutato la richiesta di finalizzare caricamento; riprovando...",
		"u_ehssrch": "il server ha rifiutato la richiesta di eseguire ricerca; riprovando...",
		"u_ehsinit": "il server ha rifiutato la richiesta di iniziare caricamento; riprovando...",
		"u_eneths": "errore di rete durante handshake per upload; riprovando...",
		"u_enethd": "errore di rete durante test esistenza target; riprovando...",
		"u_cbusy": "aspettando che il server si fidi di noi di nuovo dopo un problema di rete...",
		"u_ehsdf": "il server ha finito lo spazio su disco!\n\ncontinuerò a riprovare, nel caso qualcuno\nliberi abbastanza spazio per continuare",
		"u_emtleak1": "sembra che il tuo browser possa avere un memory leak;\nper favore",
		"u_emtleak2": ' <a href="{0}">passa a https (raccomandato)</a> o ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'prova quanto segue:\n<ul><li>premi <code>F5</code> per aggiornare la pagina</li><li>poi disabilita il pulsante &nbsp;<code>mt</code>&nbsp; nelle &nbsp;<code>⚙️ impostazioni</code></li><li>e riprova quel caricamento</li></ul>I caricamenti saranno un po\' più lenti, ma pazienza.\nScusa per il disturbo !\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">ha un bugfix</a> per questo',
		"u_emtleakf": 'prova quanto segue:\n<ul><li>premi <code>F5</code> per aggiornare la pagina</li><li>poi abilita <code>🥔</code> (patata) nell\'UI caricamento<li>e riprova quel caricamento</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">avrà sperabilmente un bugfix</a> ad un certo punto',
		"u_s404": "non trovato sul server",
		"u_expl": "spiega",
		"u_maxconn": "la maggior parte dei browser limita questo a 6, ma firefox ti permette di alzarlo con <code>connections-per-server</code> in <code>about:config</code>",
		"u_tu": '<p class="warn">AVVISO: turbo abilitato, <span>&nbsp;client potrebbe non rilevare e riprendere caricamenti incompleti; vedi tooltip pulsante turbo</span></p>',
		"u_ts": '<p class="warn">AVVISO: turbo abilitato, <span>&nbsp;risultati ricerca possono essere incorretti; vedi tooltip pulsante turbo</span></p>',
		"u_turbo_c": "turbo è disabilitato nella configurazione server",
		"u_turbo_g": "disabilitando turbo perché non hai\nprivilegi di elenco directory all'interno di questo volume",
		"u_life_cfg": 'auto-elimina dopo <input id="lifem" p="60" /> min (o <input id="lifeh" p="3600" /> ore)',
		"u_life_est": 'caricamento sarà eliminato <span id="lifew" tt="ora locale">---</span>',
		"u_life_max": 'questa cartella impone una\nvita massima di {0}',
		"u_unp_ok": 'unpost è permesso per {0}',
		"u_unp_ng": 'unpost NON sarà permesso',
		"ue_ro": 'il tuo accesso a questa cartella è solo-Lettura\n\n',
		"ue_nl": 'attualmente non sei loggato',
		"ue_la": 'attualmente sei loggato come "{0}"',
		"ue_sr": 'attualmente sei in modalità file-search\n\npassa alla modalità upload cliccando la lente d\'ingrandimento 🔎 (accanto al grande pulsante CERCA), e prova a caricare di nuovo\n\nscusa',
		"ue_ta": 'prova a caricare di nuovo, dovrebbe funzionare ora',
		"ue_ab": "questo file è già in caricamento in un'altra cartella, e quel caricamento deve essere completato prima che il file possa essere caricato altrove.\n\nPuoi interrompere e dimenticare il caricamento iniziale usando l'🧯 in alto a sinistra",
		"ur_1uo": "OK: File caricato con successo",
		"ur_auo": "OK: Tutti i {0} file caricati con successo",
		"ur_1so": "OK: File trovato sul server",
		"ur_aso": "OK: Tutti i {0} file trovati sul server",
		"ur_1un": "Caricamento fallito, scusa",
		"ur_aun": "Tutti i {0} caricamenti falliti, scusa",
		"ur_1sn": "File NON trovato sul server",
		"ur_asn": "I {0} file NON sono stati trovati sul server",
		"ur_um": "Finito;\n{0} caricamenti OK,\n{1} caricamenti falliti, scusa",
		"ur_sm": "Finito;\n{0} file trovati sul server,\n{1} file NON trovati sul server",

		"lang_set": "aggiornare per rendere effettivo il cambiamento?",
	},
	"kor": {
		"tt": "한국어",

		"cols": {
			"c": "작업 버튼",
			"dur": "길이",
			"q": "품질/비트레이트",
			"Ac": "오디오 코덱",
			"Vc": "비디오 코덱",
			"Fmt": "형식/컨테이너",
			"Ahash": "오디오 체크섬",
			"Vhash": "비디오 체크섬",
			"Res": "해상도",
			"T": "파일 유형",
			"aq": "오디오 품질/비트레이트",
			"vq": "비디오 품질/비트레이트",
			"pixfmt": "서브샘플링/픽셀 구조",
			"resw": "가로 해상도",
			"resh": "세로 해상도",
			"chs": "오디오 채널",
			"hz": "샘플레이트"
		},

		"hks": [
			[
				"기타",
				["ESC", "다양한 창 닫기"],

				"파일 관리자",
				["G", "목록/그리드 보기 전환"],
				["T", "썸네일/아이콘 전환"],
				["⇧ A/D", "썸네일 이미지 크기"],
				["ctrl-K", "선택 항목 삭제"],
				["ctrl-X", "선택 항목 잘라내기"],
				["ctrl-C", "선택 항목 복사"],
				["ctrl-V", "여기에 붙여넣기 (이동/복사)"],
				["Y", "선택 항목 다운로드"],
				["F2", "선택 항목 이름 바꾸기"],

				"파일 목록 선택",
				["space", "파일 선택/해제"],
				["↑/↓", "선택 커서 이동"],
				["ctrl ↑/↓", "커서와 뷰포트 동시 이동"],
				["⇧ ↑/↓", "이전/다음 파일 선택"],
				["ctrl-A", "모든 파일/폴더 선택"],
			], [
				"탐색",
				["B", "브레드크럼/탐색창 전환"],
				["I/K", "이전/다음 폴더"],
				["M", "상위 폴더 (또는 현재 항목 닫기)"],
				["V", "탐색창에 폴더/텍스트 파일 표시 전환"],
				["A/D", "탐색창 크기"],
			], [
				"오디오 플레이어",
				["J/L", "이전/다음 곡"],
				["U/O", "10초 뒤로/앞으로 건너뛰기"],
				["0..9", "0%..90% 지점으로 이동"],
				["P", "재생/일시정지 (시작 포함)"],
				["S", "재생 중인 곡 선택"],
				["Y", "곡 다운로드"],
			], [
				"이미지 뷰어",
				["J/L, ←/→", "이전/다음 이미지"],
				["Home/End", "첫/마지막 이미지"],
				["F", "전체 화면"],
				["R", "시계 방향으로 회전"],
				["⇧ R", "반시계 방향으로 회전"],
				["S", "이미지 선택"],
				["Y", "이미지 다운로드"],
			], [
				"비디오 플레이어",
				["U/O", "10초 뒤로/앞으로 건너뛰기"],
				["P/K/Space", "재생/일시정지"],
				["C", "다음 파일 계속 재생"],
				["V", "반복"],
				["M", "음소거"],
				["[ 와 ]", "반복 구간 설정"],
			], [
				"텍스트 파일 뷰어",
				["I/K", "이전/다음 파일"],
				["M", "텍스트 파일 닫기"],
				["E", "텍스트 파일 편집"],
				["S", "파일 선택 (잘라내기/복사/이름 바꾸기용)"],
			]
		],

		"m_ok": "확인",
		"m_ng": "취소",

		"enable": "활성화",
		"danger": "위험",
		"clipped": "클립보드에 복사되었습니다",

		"ht_s1": "초",
		"ht_s2": "초",
		"ht_m1": "분",
		"ht_m2": "분",
		"ht_h1": "시간",
		"ht_h2": "시간",
		"ht_d1": "일",
		"ht_d2": "일",
		"ht_and": " ",

		"goh": "제어판",
		"gop": '이전 형제 폴더">이전',
		"gou": '상위 폴더">위로',
		"gon": '다음 폴더">다음',
		"logout": "로그아웃 ",
		"login": "로그인", //m
		"access": " 액세스",
		"ot_close": "하위 메뉴 닫기",
		"ot_search": "속성, 경로/이름, 음악 태그 또는 이들의 조합으로 파일을 검색합니다.$N$N&lt;code&gt;foo bar&lt;/code&gt; = «foo»와 «bar»를 모두 포함해야 함,$N&lt;code&gt;foo -bar&lt;/code&gt; = «foo»는 포함하지만 «bar»는 포함하지 않아야 함,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = «yana»로 시작하고 «opus» 파일이어야 함$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = 정확히 «try unite»를 포함해야 함$N$N날짜 형식은 ISO-8601입니다. 예:$N&lt;code&gt;2009-12-31&lt;/code&gt; 또는 &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "주워담기: 최근 업로드한 항목을 삭제하거나 미완료된 업로드를 중단합니다",
		"ot_bup": "bup: 기본 업로더. 넷스케이프 4.0도 지원합니다",
		"ot_mkdir": "mkdir: 새 디렉터리를 만듭니다",
		"ot_md": "new-md: 새 마크다운 문서를 만듭니다",
		"ot_msg": "msg: 서버 로그에 메시지를 보냅니다",
		"ot_mp": "미디어 플레이어 옵션",
		"ot_cfg": "구성 옵션",
		"ot_u2i": 'up2k: (쓰기 권한이 있는 경우) 파일을 업로드하거나, 검색 모드로 전환하여 서버 어딘가에 파일이 있는지 확인합니다.$N$N업로드는 재개 가능하고, 멀티스레드로 작동하며, 파일 타임스탬프가 보존되지만, [🎈] (기본 업로더)보다 CPU를 더 많이 사용합니다.<br /><br />업로드 중에는 이 아이콘이 진행률 표시창이 됩니다!',
		"ot_u2w": 'up2k: 이어올리기 기능을 지원하는 파일 업로더입니다 (브라우저를 닫았다가 나중에 동일한 파일을 끌어다 놓으세요).$N$N멀티스레드로 작동하며, 파일 타임스탬프가 보존되지만, [🎈] (기본 업로더)보다 CPU를 더 많이 사용합니다.<br /><br />업로드 중에는 이 아이콘이 진행률 표시창이 됩니다!',
		"ot_noie": 'Chrome / Firefox / Edge를 사용해주세요',

		"ab_mkdir": "디렉터리 만들기",
		"ab_mkdoc": "새 마크다운 문서",
		"ab_msg": "서버 로그에 메시지 보내기",

		"ay_path": "폴더로 건너뛰기",
		"ay_files": "파일로 건너뛰기",

		"wt_ren": "선택한 항목 이름 바꾸기$N단축키: F2",
		"wt_del": "선택한 항목 삭제$N단축키: ctrl-K",
		"wt_cut": "선택한 항목 잘라내기 &lt;small&gt;(다른 곳에 붙여넣기용)&lt;/small&gt;$N단축키: ctrl-X",
		"wt_cpy": "선택한 항목 클립보드에 복사$N(다른 곳에 붙여넣기용)$N단축키: ctrl-C",
		"wt_pst": "이전에 잘라내거나 복사한 항목 붙여넣기$N단축키: ctrl-V",
		"wt_selall": "모든 파일 선택$N단축키: ctrl-A (파일에 포커스된 경우)",
		"wt_selinv": "선택 반전",
		"wt_zip1": "이 폴더를 압축 파일로 다운로드",
		"wt_selzip": "선택 항목을 압축 파일로 다운로드",
		"wt_seldl": "선택 항목을 개별 파일로 다운로드$N단축키: Y",
		"wt_npirc": "IRC 형식 트랙 정보 복사",
		"wt_nptxt": "일반 텍스트 트랙 정보 복사",
		"wt_m3ua": "m3u 재생 목록에 추가 (나중에 <code>📻복사</code> 클릭)",
		"wt_m3uc": "m3u 재생 목록을 클립보드에 복사",
		"wt_grid": "그리드/목록 보기 전환$N단축키: G",
		"wt_prev": "이전 트랙$N단축키: J",
		"wt_play": "재생/일시정지$N단축키: P",
		"wt_next": "다음 트랙$N단축키: L",

		"ul_par": "동시 업로드:",
		"ut_rand": "파일명 무작위로 만들기",
		"ut_u2ts": "사용자 파일 시스템의 마지막 수정 타임스탬프를$N서버에 복사\">📅",
		"ut_ow": "서버에 있는 기존 파일을 덮어쓸까요?$N🛡️: 안 함 (대신 새 파일 이름 생성)$N🕒: 서버 파일이 더 오래된 경우 덮어쓰기$N♻️: 파일이 다르면 항상 덮어쓰기",
		"ut_mt": "업로드 중 다른 파일 해싱 계속하기$N$NCPU 또는 HDD가 병목 현상을 일으키는 경우 비활성화하세요",
		"ut_ask": '업로드 시작 전 확인 요청">💭',
		"ut_pot": "느린 기기에서 UI를 단순화하여$N업로드 속도 향상",
		"ut_srch": "실제로 업로드하는 대신, 파일이 이미 서버에 있는지 확인합니다$N(읽을 수 있는 모든 폴더를 스캔합니다)",
		"ut_par": "0으로 설정하여 업로드 일시정지$N$N연결이 느리거나 지연 시간이 길면 늘리세요$N$NLAN 환경이거나 서버 HDD가 병목 현상을 일으키면 1로 유지하세요",
		"ul_btn": "파일/폴더를 여기에<br>끌어다 놓거나 클릭하세요",
		"ul_btnu": "업 로 드",
		"ul_btns": "검 색",

		"ul_hash": "해싱",
		"ul_send": "전송",
		"ul_done": "완료",
		"ul_idle1": "대기 중인 업로드가 없습니다",
		"ut_etah": "평균 &lt;em&gt;해싱&lt;/em&gt; 속도 및 예상 완료 시간",
		"ut_etau": "평균 &lt;em&gt;업로드&lt;/em&gt; 속도 및 예상 완료 시간",
		"ut_etat": "평균 &lt;em&gt;총&lt;/em&gt; 속도 및 예상 완료 시간",

		"uct_ok": "성공적으로 완료됨",
		"uct_ng": "문제 발생: 실패/거부/찾을 수 없음",
		"uct_done": "완료됨 (성공 및 문제 발생 포함)",
		"uct_bz": "해싱 또는 업로드 중",
		"uct_q": "대기 중, 보류 중",

		"utl_name": "파일명",
		"utl_ulist": "목록",
		"utl_ucopy": "복사",
		"utl_links": "링크",
		"utl_stat": "상태",
		"utl_prog": "진행률",

		// keep short:
		"utl_404": "404",
		"utl_err": "오류",
		"utl_oserr": "OS 오류",
		"utl_found": "찾음",
		"utl_defer": "보류",
		"utl_yolo": "YOLO",
		"utl_done": "완료",

		"ul_flagblk": "파일이 대기열에 추가되었습니다.</b><br>하지만 다른 브라우저 탭에서 up2k가 실행 중이므로,<br>해당 작업이 끝날 때까지 기다립니다.",
		"ul_btnlk": "서버 구성에서 이 스위치를 현재 상태로 잠갔습니다.",

		"udt_up": "업로드",
		"udt_srch": "검색",
		"udt_drop": "여기에 놓으세요",

		"u_nav_m": '<h6>자, 갖고 있는 게 무엇인가?</h6><code>Enter</code> = 파일 (하나 이상)\n<code>ESC</code> = 폴더 하나 (하위 폴더 포함)',
		"u_nav_b": '<a href="#" id="modal-ok">파일</a><a href="#" id="modal-ng">폴더 하나</a>',

		"cl_opts": "스위치",
		"cl_themes": "테마",
		"cl_langs": "언어",
		"cl_ziptype": "폴더 다운로드",
		"cl_uopts": "up2k 스위치",
		"cl_favico": "파비콘",
		"cl_bigdir": "큰 디렉터리",
		"cl_hsort": "#sort",
		"cl_keytype": "조성 표기법",
		"cl_hiddenc": "숨겨진 열",
		"cl_hidec": "숨기기",
		"cl_reset": "초기화",
		"cl_hpick": "아래 테이블에서 숨기고 싶은 열의 헤더를 탭하세요",
		"cl_hcancel": "열 숨기기가 중단되었습니다",

		"ct_grid": "田 그리드",
		"ct_ttips": '◔ ◡ ◔">ℹ️ 도움말',
		"ct_thumb": '그리드 보기에서 아이콘 또는 미리보기 이미지 전환$N단축키: T">🖼️ 미리보기',
		"ct_csel": '그리드 보기에서 CTRL과 SHIFT를 사용하여 파일 선택">선택',
		"ct_ihop": '이미지 뷰어를 닫으면 마지막으로 본 파일로 스크롤">g⮯',
		"ct_dots": '숨김 파일 표시 (서버가 허용하는 경우)">숨김파일',
		"ct_qdel": '파일 삭제 시 한 번만 확인 요청">빠른삭제',
		"ct_dir1st": '폴더를 파일보다 먼저 정렬">📁 먼저',
		"ct_nsort": '자연어 정렬 (파일명의 숫자를 인식)">자연어정렬',
		"ct_utc": '모든 날짜/시간을 UTC로 표시">UTC',
		"ct_readme": '폴더 목록에 README.md 표시">📜 readme',
		"ct_idxh": '폴더 목록 대신 index.html 표시">htm',
		"ct_sbars": '스크롤바 표시">⟊',

		"cut_umod": '파일이 서버에 이미 있는 경우, 서버의 마지막 수정 타임스탬프를 로컬 파일과 일치하도록 업데이트합니다 (쓰기+삭제 권한 필요).\">re📅',

		"cut_turbo": 'YOLO 버튼. 아마 활성화하고 싶지 않으실 겁니다.$N$N대량의 파일을 업로드하다가 어떤 이유로 재시작해야 할 때, 최대한 빨리 업로드를 계속하고 싶을 때 사용하세요.$N$N이 옵션은 해시 확인을 단순히 <em>&quot;서버에 동일한 파일 크기를 가진 파일이 있는가?&quot;</em>로 대체하므로, 파일 내용만 다를 경우 업로드되지 않습니다.$N$N업로드가 끝나면 이 옵션을 끄고, 동일한 파일을 다시 \"업로드\"하여 클라이언트가 검증하도록 해야 합니다.\">turbo',

		"cut_datechk": '터보 버튼이 활성화되어 있지 않으면 효과가 없습니다.$N$NYOLO의 위험성을 약간 줄여줍니다. 서버의 파일 타임스탬프가 사용자의 것과 일치하는지 확인합니다.$N$N<em>이론적으로는</em> 대부분의 미완료/손상된 업로드를 잡아내지만, 터보를 비활성화하고 검증 과정을 거치는 것을 대체할 수는 없습니다.\">날짜확인',

		"cut_u2sz": "각 업로드 청크의 크기 (MiB)입니다. 큰 값은 태평양을 건너는 데 더 유리합니다. 매우 불안정한 연결에서는 낮은 값을 시도해보세요.",

		"cut_flag": '한 번에 하나의 탭만 업로드하도록 보장합니다.$N-- 다른 탭도 이 옵션을 활성화해야 합니다.$N-- 동일한 도메인의 탭에만 영향을 미칩니다.',

		"cut_az": '가장 작은 파일 우선이 아닌 알파벳 순서로 파일을 업로드합니다.$N$N알파벳 순서는 서버에서 문제가 발생했는지 눈으로 확인하기 쉽게 해주지만, 광랜/LAN 환경에서는 업로드 속도가 약간 느려집니다.',

		"cut_nag": '업로드 완료 시 OS 알림$N(브라우저나 탭이 활성화되지 않은 경우에만)',
		"cut_sfx": '업로드 완료 시 소리 알림$N(브라우저나 탭이 활성화되지 않은 경우에만)',

		"cut_mt": '멀티스레딩을 사용하여 파일 해싱 속도를 높입니다.$N$N이 기능은 웹 워커를 사용하며$N더 많은 RAM이 필요합니다 (추가적으로 최대 512 MiB).$N$Nhttps는 30% 더 빠르게, http는 4.5배 더 빠르게 만듭니다.\">mt',

		"cut_wasm": '브라우저 내장 해셔 대신 wasm을 사용합니다. 크롬 기반 브라우저에서 속도를 향상시키지만 CPU 부하를 증가시키며, 많은 구버전 크롬에는 이 기능을 활성화하면 모든 RAM을 소모하고 충돌하는 버그가 있습니다.\">wasm',

		"cft_text": "파비콘 텍스트 (비워두고 새로고침하면 비활성화됨)",
		"cft_fg": "전경색",
		"cft_bg": "배경색",

		"cdt_lim": "폴더에 표시할 최대 파일 수",
		"cdt_ask": "맨 아래로 스크롤할 때$N더 많은 파일을 불러오는 대신$N무엇을 할지 묻기",
		"cdt_hsort": "미디어 URL에 포함할 정렬 규칙 (&lt;code&gt;,sorthref&lt;/code&gt;)의 수. 0으로 설정하면 미디어 링크를 클릭할 때 포함된 정렬 규칙도 무시됩니다.",

		"tt_entree": "탐색 창 (디렉터리 트리 사이드바) 표시$N단축키: B",
		"tt_detree": "이동 경로 표시$N단축키: B",
		"tt_visdir": "선택한 폴더로 스크롤하기",
		"tt_ftree": "폴더 트리/텍스트 파일 전환$N단축키: V",
		"tt_pdock": "상위 폴더를 상단에 고정된 창에 표시",
		"tt_dynt": "트리가 확장될 때 자동으로 너비 증가",
		"tt_wrap": "자동 줄 바꿈",
		"tt_hover": "마우스를 올리면 넘어가는 줄 표시$N(마우스 커서가 왼쪽 여백에$N&nbsp; 있지 않으면 스크롤이 깨짐)",

		"ml_pmode": "폴더 끝에서...",
		"ml_btns": "명령",
		"ml_tcode": "트랜스코딩",
		"ml_tcode2": "다음으로 트랜스코딩",
		"ml_tint": "틴트",
		"ml_eq": "오디오 이퀄라이저",
		"ml_drc": "다이내믹 레인지 압축기",

		"mt_loop": "한 곡 반복 재생\">🔁",
		"mt_one": "한 곡 재생 후 중지\">1️⃣",
		"mt_shuf": "각 폴더의 곡을 무작위 재생\">🔀",
		"mt_aplay": "서버에 접속한 링크에 곡 ID가 있으면 자동 재생$N$N이것을 비활성화하면 음악 재생 시 페이지 URL이 곡 ID로 업데이트되지 않아, 이 설정이 손실되고 URL이 남아있을 경우 자동 재생되는 것을 방지합니다.\">a▶",
		"mt_preload": "끊김 없는 재생을 위해 다음 곡을 미리 불러오기 시작\">미리로드",
		"mt_prescan": "마지막 곡이 끝나기 전에 다음 폴더로 이동하여$N웹브라우저가 재생을 멈추지 않도록 합니다.\">탐색",
		"mt_fullpre": "전체 곡을 미리 불러오기 시도;$N✅ <b>불안정한</b> 연결에서 활성화,$N❌ <b>느린</b> 연결에서는 아마도 비활성화\">전체",
		"mt_fau": "폰에서 다음 곡이 충분히 빨리 미리 불러오지 않아 음악이 멈추는 것을 방지합니다 (태그 표시가 불안정해질 수 있음).\">☕️",
		"mt_waves": "파형 탐색 바:$N탐색 바에 오디오 진폭 표시\">~s",
		"mt_npclip": "현재 재생 중인 곡을 클립보드에 복사하는 버튼 표시\">/np",
		"mt_m3u_c": "선택한 곡을 m3u8 재생 목록 항목으로$N클립보드에 복사하는 버튼 표시\">📻",
		"mt_octl": "OS 통합 (미디어 단축키/OSD)\">os-ctl",
		"mt_oseek": "OS 통합을 통해 탐색 허용$N$N참고: 일부 기기 (iPhone)에서는$N이것이 다음 곡 버튼을 대체합니다.\">탐색",
		"mt_oscv": "OSD에 앨범 커버 표시\">아트",
		"mt_follow": "재생 중인 트랙이 보이도록 스크롤 유지\">🎯",
		"mt_compact": "컴팩트 컨트롤\">⟎",
		"mt_uncache": "캐시 지우기 (브라우저가 곡의 깨진 사본을 캐시하여$N재생이 안되는 경우 시도해보세요)\">캐시삭제",
		"mt_mloop": "열린 폴더 반복\">🔁 반복",
		"mt_mnext": "다음 폴더 불러오고 계속\">📂 다음",
		"mt_mstop": "재생 중지\">⏸ 중지",
		"mt_cflac": "flac/wav를 {0}로 변환\">flac",
		"mt_caac": "aac/m4a를 {0}로 변환\">aac",
		"mt_coth": "다른 모든 것 (mp3 제외)을 {0}로 변환\">기타",
		"mt_c2opus": "데스크톱, 노트북, 안드로이드 환경에 최적\">opus",
		"mt_c2owa": "iOS 17.5 이상용 opus-weba\">owa",
		"mt_c2caf": "iOS 11부터 17까지용 opus-caf\">caf",
		"mt_c2mp3": "매우 오래된 기기에서 사용\">mp3",
		"mt_c2flac": "최고 음질이지만 다운로드 용량이 큼\">flac",
		"mt_c2wav": "비압축 재생 (더 큼)\">wav",
		"mt_c2ok": "네, 좋은 선택입니다",
		"mt_c2nd": "기기에 권장되는 출력 형식이 아니지만 괜찮습니다",
		"mt_c2ng": "기기가 이 출력 형식을 지원하지 않는 것 같지만, 시도해 보겠습니다",
		"mt_xowa": "iOS에서 이 형식의 백그라운드 재생이 안되는 버그가 있습니다. 대신 caf나 mp3를 사용해주세요.",
		"mt_tint": "탐색 바의 배경 레벨 (0-100)$N버퍼링이 덜 눈시리게 만듦",
		"mt_eq": "이퀄라이저 및 게인 제어 활성화;$N$Nboost &lt;code&gt;0&lt;/code&gt; = 표준 100% 볼륨 (수정 없음)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = 표준 스테레오 (수정 없음)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% 좌우 크로스피드$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = 모노$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = 보컬 제거 :^)$N$N이퀄라이저를 활성화하면 끊김 없는 앨범이 온전히 끊김 없이 재생되므로, 그 점이 중요하다면 모든 값을 0으로 두고 (width=1 제외) 켜두세요.",
		"mt_drc": "다이내믹 레인지 컴프레서(볼륨 평탄화/벽돌화)를 활성화합니다. 스파게티의 균형을 맞추기 위해 EQ도 활성화되므로, 원하지 않으면 'width'를 제외한 모든 EQ 필드를 0으로 설정하세요.$N$NTHRESHOLD dB 이상의 오디오 볼륨을 낮춥니다. THRESHOLD를 초과하는 모든 RATIO dB에 대해 1dB의 출력이 있으므로, 기본값인 tresh -24 및 ratio 12는 볼륨이 -22dB보다 커지지 않음을 의미하며, 이퀄라이저 부스트를 0.8 또는 ATK 0과 큰 RLS (예: 90)를 사용하여 1.8까지 안전하게 높일 수 있습니다 (firefox에서만 작동, 다른 브라우저에서는 RLS 최대 1).$N$N(위키백과를 참조하세요, 훨씬 더 잘 설명되어 있습니다)",

		"mb_play": "재생",
		"mm_hashplay": "이 오디오 파일을 재생할까요?",
		"mm_m3u": "<code>Enter/확인</code>을 눌러 재생\n<code>ESC/취소</code>를 눌러 편집",
		"mp_breq": "Firefox 82+, Chrome 73+ 또는 iOS 15+ 필요",
		"mm_bload": "불러오는 중...",
		"mm_bconv": "{0}(으)로 변환 중, 잠시만 기다려주세요...",
		"mm_opusen": "브라우저가 aac/m4a 파일을 재생할 수 없습니다.\nopus로의 트랜스코딩이 활성화되었습니다.",
		"mm_playerr": "재생 실패: ",
		"mm_eabrt": "재생 시도가 취소되었습니다",
		"mm_enet": "인터넷 연결이 불안정합니다",
		"mm_edec": "이 파일이 손상된 것 같습니다??",
		"mm_esupp": "브라우저가 이 오디오 형식을 이해하지 못합니다",
		"mm_eunk": "알 수 없는 오류",
		"mm_e404": "오디오를 재생할 수 없습니다; 오류 404: 파일을 찾을 수 없습니다.",
		"mm_e403": "오디오를 재생할 수 없습니다; 오류 403: 접근이 거부되었습니다.\n\nF5를 눌러 새로고침 해보세요, 로그아웃되었을 수 있습니다",
		"mm_e500": "오디오를 재생할 수 없습니다; 오류 500: 서버 로그를 확인하세요.",
		"mm_e5xx": "오디오를 재생할 수 없습니다; 서버 오류 ",
		"mm_nof": "주변에서 더 이상 오디오 파일을 찾을 수 없습니다",
		"mm_prescan": "다음에 재생할 음악을 찾는 중...",
		"mm_scank": "다음 곡을 찾았습니다:",
		"mm_uncache": "캐시가 지워졌습니다. 모든 곡은 다음 재생 시 다시 다운로드됩니다.",
		"mm_hnf": "그 곡이 더 이상 존재하지 않습니다",

		"im_hnf": "그 이미지가 더 이상 존재하지 않습니다",

		"f_empty": '이 폴더는 비어 있습니다',
		"f_chide": '«{0}» 열을 숨깁니다.\n\n설정 탭에서 열을 다시 표시할 수 있습니다.',
		"f_bigtxt": "이 파일은 {0} MiB입니다 -- 정말 텍스트로 보시겠습니까?",
		"f_bigtxt2": "대신 파일의 끝부분만 보시겠습니까? 이렇게 하면 실시간으로 새로 추가되는 텍스트 줄을 보여주는 팔로잉/테일링 기능도 활성화됩니다.",
		"fbd_more": '<div id="blazy"><code>{1}</code>개 파일 중 <code>{0}</code>개 표시 중; <a href="#" id="bd_more">{2}개 더 보기</a> 또는 <a href="#" id="bd_all">모두 보기</a></div>',
		"fbd_all": '<div id="blazy"><code>{1}</code>개 파일 중 <code>{0}</code>개 표시 중; <a href="#" id="bd_all">모두 보기</a></div>',
		"f_anota": "{1}개 항목 중 {0}개만 선택되었습니다.\n전체 폴더를 선택하려면 먼저 맨 아래로 스크롤하세요.",

		"f_dls": '현재 폴더의 파일 링크가\n다운로드 링크로 변경되었습니다',

		"f_partial": "현재 업로드 중인 파일을 안전하게 다운로드하려면, 파일 이름이 같지만 <code>.PARTIAL</code> 확장자가 없는 파일을 클릭하세요. 이 경고를 무시하려면 \"취소\" 또는 ESC를 누르세요.\n\n\"확인\"/Enter를 누르면 이 경고를 무시하고 <code>.PARTIAL</code> 임시 파일을 계속 다운로드하며, 이 경우 거의 확실히 손상된 데이터를 받게 됩니다.",

		"ft_paste": "{0}개 항목 붙여넣기$N단축키: ctrl-V",
		"fr_eperm": "이름을 바꿀 수 없습니다:\n이 폴더에 \"이동\" 권한이 없습니다",
		"fd_eperm": "삭제할 수 없습니다:\n이 폴더에 \"삭제\" 권한이 없습니다",
		"fc_eperm": "잘라낼 수 없습니다:\n이 폴더에 \"이동\" 권한이 없습니다",
		"fp_eperm": "붙여넣을 수 없습니다\n이 폴더에 \"쓰기\" 권한이 없습니다",
		"fr_emore": "이름을 바꿀 항목을 하나 이상 선택하세요",
		"fd_emore": "삭제할 항목을 하나 이상 선택하세요",
		"fc_emore": "잘라낼 항목을 하나 이상 선택하세요",
		"fcp_emore": "클립보드에 복사할 항목을 하나 이상 선택하세요",

		"fs_sc": "현재 폴더 공유",
		"fs_ss": "선택한 파일 공유",
		"fs_just1d": "하나 이상의 폴더를 선택하거나,\n파일과 폴더를 한 번에 섞어 선택할 수 없습니다",
		"fs_abrt": "❌ 중단",
		"fs_rand": "🎲 무작위 이름",
		"fs_go": "✅ 공유 생성",
		"fs_name": "이름",
		"fs_src": "소스",
		"fs_pwd": "비밀번호",
		"fs_exp": "만료",
		"fs_tmin": "분",
		"fs_thrs": "시간",
		"fs_tdays": "일",
		"fs_never": "영원",
		"fs_pname": "선택적 링크 이름; 비워두면 무작위로 생성",
		"fs_tsrc": "공유할 파일 또는 폴더",
		"fs_ppwd": "비밀번호 (선택사항)",
		"fs_w8": "공유 생성 중...",
		"fs_ok": "<code>Enter/OK</code>를 눌러 클립보드에 복사\n<code>ESC/Cancel</code>를 눌러 닫기",

		"frt_dec": "깨진 파일 이름의 일부 경우를 수정할 수 있습니다\">url-디코드",
		"frt_rst": "수정된 파일 이름을 원래대로 되돌립니다\">↺ 초기화",
		"frt_abrt": "이 창을 중단하고 닫습니다\">❌ 취소",
		"frb_apply": "이름 바꾸기 적용",
		"fr_adv": "배치/메타데이터/패턴 이름 바꾸기\">고급",
		"fr_case": "대소문자 구분 정규식\">대소문자",
		"fr_win": "Windows 안전 이름; <code>&lt;&gt;:&quot;\\|?*</code>를 일본어 전각 문자로 바꿉니다\">win",
		"fr_slash": "<code>/</code>를 새 폴더를 만들지 않는 문자로 바꿉니다\">/ 없음",
		"fr_re": "원본 파일 이름에 적용할 정규식 검색 패턴; 캡처링 그룹은 아래 형식 필드에서 &lt;code&gt;(1)&lt;/code&gt;, &lt;code&gt;(2)&lt;/code&gt; 등으로 참조할 수 있습니다",
		"fr_fmt": "foobar2000에서 영감을 받음:$N&lt;code&gt;(title)&lt;/code&gt;은(는) 곡 제목으로 대체됨,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt;은(는) 아티스트가 비어 있으면 [이] 부분을 건너뜀$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt;은(는) 트랙 번호를 2자리로 채움",
		"fr_pdel": "삭제",
		"fr_pnew": "다른 이름으로 저장",
		"fr_pname": "새 프리셋의 이름을 입력하세요",
		"fr_aborted": "중단됨",
		"fr_lold": "이전 이름",
		"fr_lnew": "새 이름",
		"fr_tags": "선택한 파일의 태그 (읽기 전용, 참조용):",
		"fr_busy": "{0}개 항목 이름 바꾸는 중...\n\n{1}",
		"fr_efail": "이름 바꾸기 실패:\n",
		"fr_nchg": "<code>win</code> 및/또는 <code>/ 없음</code>으로 인해 새 이름 중 {0}개가 변경되었습니다.\n\n이 변경된 새 이름으로 계속하시겠습니까?",

		"fd_ok": "삭제 확인",
		"fd_err": "삭제 실패:\n",
		"fd_none": "아무것도 삭제되지 않았습니다. 서버 구성 (xbd)에 의해 차단되었을 수 있습니다.",
		"fd_busy": "삭제 중 {0}개 항목...\n\n{1}",
		"fd_warn1": "이 {0}개 항목을 삭제하시겠습니까?",
		"fd_warn2": "<b>마지막 기회입니다!</b> 되돌릴 수 없습니다. 삭제하시겠습니까?",

		"fc_ok": "{0}개 항목 잘라내기 완료",
		"fc_warn": "{0}개 항목 잘라내기 완료\n\n하지만: 선택 항목이 너무 커서 <b>이</b> 브라우저 탭에서만 붙여넣을 수 있습니다",

		"fcc_ok": "{0}개 항목을 클립보드에 복사했습니다",
		"fcc_warn": "{0}개 항목을 클립보드에 복사했습니다\n\n하지만: 선택 항목이 너무 커서 <b>이</b> 브라우저 탭에서만 붙여넣을 수 있습니다",

		"fp_apply": "이 이름 사용",
		"fp_ecut": "붙여넣거나 이동하려면 먼저 파일/폴더를 잘라내거나 복사하세요\n\n참고: 다른 브라우저 탭 간에 잘라내기/붙여넣기를 할 수 있습니다",
		"fp_ename": "이름이 이미 사용 중이므로 {0}개 항목을 여기로 이동할 수 없습니다. 계속하려면 아래에 새 이름을 지정하거나, 이름을 비워두면 건너뜁니다:",
		"fcp_ename": "이름이 이미 사용 중이므로 {0}개 항목을 여기로 복사할 수 없습니다. 계속하려면 아래에 새 이름을 지정하거나, 이름을 비워두면 건너뜁니다:",
		"fp_emore": "아직 해결해야 할 파일 이름 충돌이 남아 있습니다",
		"fp_ok": "이동 완료",
		"fcp_ok": "복사 완료",
		"fp_busy": "{0}개 항목 이동 중...\n\n{1}",
		"fcp_busy": "{0}개 항목 복사 중...\n\n{1}",
		"fp_abrt": "취소 중...",
		"fp_err": "이동 실패:\n",
		"fcp_err": "복사 실패:\n",
		"fp_confirm": "이 {0}개 항목을 여기로 이동하시겠습니까?",
		"fcp_confirm": "이 {0}개 항목을 여기로 복사하시겠습니까?",
		"fp_etab": '다른 브라우저 탭에서 클립보드를 읽지 못했습니다',
		"fp_name": "기기에서 파일을 업로드합니다. 이름을 지정하세요:",
		"fp_both_m": '<h6>붙여넣을 항목 선택</h6><code>Enter</code> = «{1}»에서 파일 {0}개 이동\n<code>ESC</code> = 기기에서 파일 {2}개 업로드',
		"fcp_both_m": '<h6>붙여넣을 항목 선택</h6><code>Enter</code> = «{1}»에서 파일 {0}개 복사\n<code>ESC</code> = 기기에서 파일 {2}개 업로드',
		"fp_both_b": '<a href="#" id="modal-ok">이동</a><a href="#" id="modal-ng">업로드</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">복사</a><a href="#" id="modal-ng">업로드</a>',

		"mk_noname": "왼쪽 텍스트 필드에 이름을 먼저 입력해주세요 :p",

		"tv_load": "텍스트 문서 불러오는 중:\n\n{0}\n\n{1}% ({3} MiB 중 {2} MiB 로드됨)",
		"tv_xe1": "텍스트 파일을 불러올 수 없습니다:\n\n오류 ",
		"tv_xe2": "404, 파일을 찾을 수 없음",
		"tv_lst": "텍스트 파일 목록",
		"tvt_close": "폴더 보기로 돌아가기$N단축키: M (또는 Esc)\">❌ 닫기",
		"tvt_dl": "이 파일 다운로드$N단축키: Y\">💾 다운로드",
		"tvt_prev": "이전 문서 보기$N단축키: i\">⬆ 이전",
		"tvt_next": "다음 문서 보기$N단축키: K\">⬇ 다음",
		"tvt_sel": "파일 선택 &nbsp; (잘라내기/복사/삭제/...용)$N단축키: S\">선택",
		"tvt_edit": "텍스트 편집기에서 파일 열기$N단축키: E\">✏️ 편집",
		"tvt_tail": "파일 변경 사항 모니터링; 실시간으로 새 줄 표시\">📡 팔로우",
		"tvt_wrap": "자동 줄 바꿈\">↵",
		"tvt_atail": "페이지 하단으로 스크롤 고정\">⚓",
		"tvt_ctail": "터미널 색상 디코딩 (ANSI 이스케이프 코드)\">🌈",
		"tvt_ntail": "스크롤백 제한 (불러온 상태로 유지할 텍스트 바이트 수)",

		"m3u_add1": "m3u 재생 목록에 곡이 추가되었습니다",
		"m3u_addn": "{0}개의 곡이 m3u 재생 목록에 추가되었습니다",
		"m3u_clip": "m3u 재생 목록이 클립보드에 복사되었습니다\n\n something.m3u와 같은 이름의 새 텍스트 파일을 만들고 그 문서에 재생 목록을 붙여넣으면 재생할 수 있습니다.",

		"gt_vau": "비디오를 표시하지 않고 오디오만 재생\">🎧",
		"gt_msel": "파일 선택 활성화; ctrl-클릭하여 파일 재정의$N$N&lt;em&gt;활성 시: 파일/폴더를 두 번 클릭하여 열기&lt;/em&gt;$N$N단축키: S\">다중선택",
		"gt_crop": "썸네일 중앙 자르기\">자르기",
		"gt_3x": "고해상도 썸네일\">3x",
		"gt_zoom": "확대/축소",
		"gt_chop": "자르기",
		"gt_sort": "정렬 기준",
		"gt_name": "이름",
		"gt_sz": "크기",
		"gt_ts": "날짜",
		"gt_ext": "유형",
		"gt_c1": "파일명 더 많이 생략하기 (더 적게 표시)",
		"gt_c2": "파일명 덜 생략하기 (더 많이 표시)",

		"sm_w8": "검색 중...",
		"sm_prev": "아래 검색 결과는 이전 검색어에 대한 결과입니다:\n  ",
		"sl_close": "검색 결과 닫기",
		"sl_hits": "{0}개 결과 표시 중",
		"sl_moar": "더 불러오기",

		"s_sz": "크기",
		"s_dt": "날짜",
		"s_rd": "경로",
		"s_fn": "이름",
		"s_ta": "태그",
		"s_ua": "업로드 시점",
		"s_ad": "고급",
		"s_s1": "최소 MiB",
		"s_s2": "최대 MiB",
		"s_d1": "최소 ISO-8601",
		"s_d2": "최대 ISO-8601",
		"s_u1": "이후",
		"s_u2": "이전",
		"s_r1": "경로에 포함 &nbsp; (공백으로 구분)",
		"s_f1": "이름에 포함 &nbsp; (-로 제외)",
		"s_t1": "태그에 포함 &nbsp; (^=시작, 끝=$)",
		"s_a1": "특정 메타데이터 속성",

		"md_eshow": "렌더링할 수 없음 ",
		"md_off": "[📜<em>readme</em>]가 [⚙️]에서 비활성화됨 -- 문서 숨김",

		"badreply": "서버로부터의 응답을 구문 분석하지 못했습니다",

		"xhr403": "403: 접근 거부됨\n\nF5를 눌러보세요, 로그아웃되었을 수 있습니다",
		"xhr0": "알 수 없음 (서버와의 연결이 끊겼거나 서버가 오프라인일 수 있습니다)",
		"cf_ok": "죄송합니다 -- DD" + wah + "oS 보호 기능이 작동했습니다\n\n약 30초 후에 다시 정상적으로 작동할 것입니다\n\n아무 일도 일어나지 않으면 F5를 눌러 페이지를 새로고침하세요",
		"tl_xe1": "하위 폴더를 나열할 수 없습니다:\n\n오류 ",
		"tl_xe2": "404: 폴더를 찾을 수 없음",
		"fl_xe1": "폴더의 파일을 나열할 수 없습니다:\n\n오류 ",
		"fl_xe2": "404: 폴더를 찾을 수 없음",
		"fd_xe1": "하위 폴더를 만들 수 없습니다:\n\n오류 ",
		"fd_xe2": "404: 상위 폴더를 찾을 수 없음",
		"fsm_xe1": "메시지를 보낼 수 없습니다:\n\n오류 ",
		"fsm_xe2": "404: 상위 폴더를 찾을 수 없음",
		"fu_xe1": "서버에서 주워담기 목록을 불러오지 못했습니다:\n\n오류 ",
		"fu_xe2": "404: 파일을 찾을 수 없음??",

		"fz_tar": "압축되지 않은 gnu-tar 파일 (linux / mac)",
		"fz_pax": "압축되지 않은 pax 형식 tar (느림)",
		"fz_targz": "gzip 레벨 3 압축이 적용된 gnu-tar$N$N이것은 보통 매우 느리므로$N압축되지 않은 tar를 대신 사용하세요",
		"fz_tarxz": "xz 레벨 1 압축이 적용된 gnu-tar$N$N이것은 보통 매우 느리므로$N압축되지 않은 tar를 대신 사용하세요",
		"fz_zip8": "utf8 파일 이름이 포함된 zip (windows 7 및 이전 버전에서 문제가 있을 수 있음)",
		"fz_zipd": "정말 오래된 소프트웨어를 위한 전통적인 cp437 파일 이름이 포함된 zip",
		"fz_zipc": "MS-DOS PKZIP v2.04g (1993년 10월)용으로$Ncrc32가 미리 계산된 cp437$N(다운로드 시작 전 처리 시간이 더 걸림)",

		"un_m1": "아래에서 최근 업로드를 삭제하거나 미완료된 업로드를 중단할 수 있습니다",
		"un_upd": "새로고침",
		"un_m4": "또는 아래에 보이는 파일을 공유할 수 있습니다:",
		"un_ulist": "보기",
		"un_ucopy": "복사",
		"un_flt": "선택적 필터:&nbsp; URL에 포함되어야 함",
		"un_fclr": "필터 지우기",
		"un_derr": '주워담기-삭제 실패:\n',
		"un_f5": '문제가 발생했습니다, 새로고침하거나 F5를 눌러보세요',
		"un_uf5": "죄송하지만, 이 업로드를 중단하기 전에 페이지를 새로고침해야 합니다 (예: F5 또는 CTRL-R 누르기).",
		"un_nou": '<b>경고:</b> 서버가 너무 바빠서 미완료 업로드를 표시할 수 없습니다; 잠시 후 "새로고침" 링크를 클릭하세요',
		"un_noc": '<b>경고:</b> 완전히 업로드된 파일의 주워담기가 서버 구성에서 활성화/허용되지 않았습니다',
		"un_max": "처음 2000개 파일을 표시합니다 (필터를 사용하세요)",
		"un_avail": "{0}개의 최근 업로드를 삭제할 수 있습니다<br />{1}개의 미완료 업로드를 중단할 수 있습니다",
		"un_m2": "업로드 시간순으로 정렬됨. 가장 최근 항목이 먼저 표시:",
		"un_no1": "아쉽다! 충분히 최근인 업로드가 없습니다.",
		"un_no2": "아쉽다! 해당 필터와 일치하는 최근 업로드가 없습니다.",
		"un_next": "아래의 다음 {0}개 파일 삭제",
		"un_abrt": "중단",
		"un_del": "삭제",
		"un_m3": "최근 업로드 로드 중...",
		"un_busy": "{0}개 파일 삭제 중...",
		"un_clip": "{0}개의 링크가 클립보드에 복사되었습니다",

		"u_https1": "더 나은 성능을 위해",
		"u_https2": "https로 전환",
		"u_https3": "하는 것이 좋습니다",
		"u_ancient": '브라우저가 정말 오래되었네요 -- 아마도 <a href="#" onclick="goto(\'bup\')">bup을 대신 사용</a>해야 할 것 같습니다',
		"u_nowork": "Firefox 53+, Chrome 57+ 또는 iOS 11+가 필요합니다",
		"tail_2old": "Firefox 105+, Chrome 71+ 또는 iOS 14.5+가 필요합니다",
		"u_nodrop": '브라우저가 너무 오래되어 드래그 앤 드롭 업로드를 지원하지 않습니다',
		"u_notdir": '폴더가 아닙니다!\n\n브라우저가 너무 오래되었습니다,\n대신 드래그드롭을 시도해보세요',
		"u_uri": '다른 브라우저 창에서 이미지를 드래그드롭하려면,\n큰 업로드 버튼 위로 떨어뜨려주세요',
		"u_enpot": '<a href="#">단순 UI로 전환</a> (업로드 속도가 향상될 수 있음)',
		"u_depot": '<a href="#">화려한 UI로 전환</a> (업로드 속도가 감소할 수 있음)',
		"u_gotpot": '업로드 속도 향상을 위해 단순 UI로 전환합니다,\n\n언제든지 다시 전환하셔도 좋습니다!',
		"u_pott": "<p>파일: &nbsp; <b>{0}</b> 완료, &nbsp; <b>{1}</b> 실패, &nbsp; <b>{2}</b> 처리 중, &nbsp; <b>{3}</b> 대기 중</p>",
		"u_ever": "이것은 기본 업로더입니다. up2k는 최소한 다음 버전이 필요합니다:<br>Chrome 21 // Firefox 13 // Edge 12 // Opera 12 // Safari 5.1",
		"u_su2k": '이것은 기본 업로더입니다. <a href="#" id="u2yea">up2k</a>가 더 좋습니다',
		"u_uput": '속도 최적화 (체크섬 건너뛰기)',
		"u_ewrite": '이 폴더에 쓰기 권한이 없습니다',
		"u_eread": '이 폴더에 읽기 권한이 없습니다',
		"u_enoi": '파일 검색이 서버 구성에서 활성화되지 않았습니다',
		"u_enoow": '여기서는 덮어쓰기가 작동하지 않습니다. 삭제 권한이 필요합니다',
		"u_badf": '총 {1}개 중 다음 {0}개의 파일은 파일 시스템 권한 문제 등으로 건너뛰었습니다:\n\n',
		"u_blankf": '총 {1}개 중 다음 {0}개의 파일은 비어있습니다. 그래도 업로드하시겠습니까?\n\n',
		"u_applef": '총 {1}개 중 다음 {0}개의 파일은 아마도 불필요한 파일일 것입니다.\n다음 파일을 건너뛰려면 <code>확인/Enter</code>를 누르세요,\n해당 파일도 업로드하려면 <code>취소/ESC</code>를 누르세요:\n\n',
		"u_just1": '\n파일을 하나만 선택하면 더 잘 작동할 수 있습니다',
		"u_ff_many": '<b>리눅스/macOS/안드로이드</b>를 사용 중이라면, 이 정도의 파일 수는 <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">Firefox를 <em>충돌시킬 수 있습니다!</em></a>\n만약 그런 일이 발생하면 다시 시도하거나 Chrome을 사용해주세요.',
		"u_up_life": '이 업로드는 완료 후 {0} 뒤에\n서버에서 삭제됩니다',
		"u_asku": '이 {0}개의 파일을 <code>{1}</code>(으)로 업로드하시겠습니까?',
		"u_unpt": '왼쪽 상단의 🧯를 사용하여 이 업로드를 취소/삭제할 수 있습니다',
		"u_bigtab": '{0}개의 파일을 표시하려고 합니다\n\n브라우저가 충돌할 수 있습니다, 계속 진행합니까?',
		"u_scan": '파일 스캔 중...',
		"u_dirstuck": '디렉터리 반복자가 다음 {0}개 항목에 접근하는 데 실패하여 건너뜁니다:',
		"u_etadone": '완료 ({0}, {1}개 파일)',
		"u_etaprep": '(업로드 준비 중)',
		"u_hashdone": '해싱 완료',
		"u_hashing": '해시',
		"u_hs": '핸드셰이킹 중...',
		"u_started": '파일이 현재 업로드 중입니다. [🚀] 참조',
		"u_dupdefer": '중복됨. 다른 모든 파일 처리 후 처리됩니다',
		"u_actx": "다른 창/탭으로 전환 시 성능 저하를<br />방지하려면 이 텍스트를 클릭하세요",
		"u_fixed": "OK!&nbsp; 해결됐습니다 👍",
		"u_cuerr": "{1} 중 청크 {0} 업로드 실패;\n아마 문제 없을 겁니다. 계속 진행합니다\n\n파일: {2}",
		"u_cuerr2": "서버가 업로드를 거부했습니다 (청크 {0}/{1});\n나중에 다시 시도합니다\n\n파일: {2}\n\n오류 ",
		"u_ehstmp": "다시 시도합니다; 오른쪽 하단 참조",
		"u_ehsfin": "서버가 업로드 완료 요청을 거부했습니다. 재시도 중...",
		"u_ehssrch": "서버가 검색 수행 요청을 거부했습니다. 재시도 중...",
		"u_ehsinit": "서버가 업로드 시작 요청을 거부했습니다. 재시도 중...",
		"u_eneths": "업로드 핸드셰이크 중 네트워크 오류 발생. 재시도 중...",
		"u_enethd": "대상 존재 여부 테스트 중 네트워크 오류 발생; 재시도 중...",
		"u_cbusy": '네트워크 문제 후 서버가 다시 우리를 신뢰할 때까지 기다리는 중...',
		"u_ehsdf": '서버 디스크 공간이 부족합니다!\n\n누군가 계속할 수 있을 만큼의 공간을\n비워줄 경우를 대비해 계속 재시도합니다',
		"u_emtleak1": "웹 브라우저에 메모리 누수가 있는 것 같습니다.\n",
		"u_emtleak2": ' <a href="{0}">https로 전환 (권장)</a>하거나 ',
		"u_emtleak3": ' ',
		"u_emtleakc": '다음을 시도해보세요:\n<ul><li><code>F5</code>를 눌러 페이지를 새로고침하세요</li><li>그런 다음 <code>⚙️ 설정</code>에서 &nbsp;<code>mt</code>&nbsp; 버튼을 비활성화하세요</li><li>그리고 다시 그 업로드를 시도해보세요</li></ul>업로드가 조금 느려지겠지만, 어쩔 수 없죠.\n불편을 드려 죄송합니다!\n\nPS: 이 버그는 Chrome v107에서 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">수정되었습니다</a>.',
		"u_emtleakf": '다음을 시도해보세요:\n<ul><li><code>F5</code>를 눌러 페이지를 새로고침하세요</li><li>그런 다음 업로드 UI에서 <code>🥔</code>(단순 UI)를 활성화하세요<li>그리고 다시 그 업로드를 시도해보세요</li></ul>\nPS: Firefox에서 <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">언젠가 이 버그가 수정될 거라 믿습니다</a>.',
		"u_s404": '서버에서 찾을 수 없음',
		"u_expl": '설명',
		"u_maxconn": "대부분의 브라우저는 이를 6으로 제한하지만, Firefox에서는 <code>about:config</code>에서 <code>connections-per-server</code> 설정값으로 높일 수 있습니다.",
		"u_tu": '<p class="warn">경고: 터보가 활성화되어 <span>클라이언트가 불완전한 업로드를 감지하고 재개하지 못할 수 있습니다. 터보 버튼의 툴팁을 참조하세요</span></p>',
		"u_ts": '<p class="warn">경고: 터보가 활성화되어 <span>검색 결과가 부정확할 수 있습니다. 터보 버튼의 툴팁을 참조하세요</span></p>',
		"u_turbo_c": "터보가 서버 구성에서 비활성화되었습니다",
		"u_turbo_g": '이 볼륨 내에서 디렉터리 목록 권한이 없으므로\n터보를 비활성화합니다',
		"u_life_cfg": '자동 삭제 시간 <input id="lifem" p="60" /> 분 (또는 <input id="lifeh" p="3600" /> 시간)',
		"u_life_est": '업로드가 <span id="lifew" tt="현지 시간">---</span>에 삭제됩니다',
		"u_life_max": '이 폴더는 최대 수명을\n{0}(으)로 강제합니다',
		"u_unp_ok": '주워담기는 {0} 동안 허용됩니다',
		"u_unp_ng": '주워담기는 허용되지 않습니다',
		"ue_ro": '이 폴더에 대한 접근은 읽기 전용입니다\n\n',
		"ue_nl": '현재 로그인되어 있지 않습니다',
		"ue_la": '현재 \'{0}\'(으)로 로그인되어 있습니다',
		"ue_sr": '현재 파일 검색 모드입니다\n\n큰 "검색" 버튼 옆의 돋보기 🔎를 클릭하여 업로드 모드로 전환한 후 다시 업로드해보세요\n\n죄송합니다',
		"ue_ta": '다시 업로드해보세요, 이제 작동할 겁니다',
		"ue_ab": '이 파일은 이미 다른 폴더로 업로드 중이며, 파일이 다른 곳에 업로드되기 전에 해당 업로드가 완료되어야 합니다.\n\n왼쪽 상단의 🧯를 사용하여 초기 업로드를 중단하고 잊을 수 있습니다.',
		"ur_1uo": "OK: 파일이 성공적으로 업로드되었습니다",
		"ur_auo": "OK: 모든 {0}개의 파일이 성공적으로 업로드되었습니다",
		"ur_1so": "OK: 서버에서 파일을 찾았습니다",
		"ur_aso": "OK: 서버에서 모든 {0}개의 파일을 찾았습니다",
		"ur_1un": "업로드에 실패했습니다, 죄송",
		"ur_aun": "모든 {0}개의 업로드에 실패했습니다, 죄송",
		"ur_1sn": "서버에서 파일을 찾지 못했습니다",
		"ur_asn": "서버에서 {0}개의 파일을 찾지 못했습니다",
		"ur_um": "완료;\n{0}개 업로드 성공,\n{1}개 업로드 실패, 죄송",
		"ur_sm": "완료;\n서버에서 {0}개 파일 찾음,\n서버에서 {1}개 파일 찾지 못함",

		"lang_set": '변경 사항을 적용하기 위해 새로고침하시겠습니까?'
	},
	"nld": {
		"tt": "Nederlands",

		"cols": {
			"c": "Action knoppen",
			"dur": "Duratie",
			"q": "Kwaliteit / bitrate",
			"Ac": "Audio codec",
			"Vc": "Video codec",
			"Fmt": "Formaat / container",
			"Ahash": "Audio checksum",
			"Vhash": "Video checksum",
			"Res": "Resolution",
			"T": "Bestandstype",
			"aq": "Audio kwaliteit / bitrate",
			"vq": "Video kwaliteit / bitrate",
			"pixfmt": "Subsampling / pixel structure",
			"resw": "Horizontale resolutie",
			"resh": "Verticale resolutie",
			"chs": "Audiokanalen",
			"hz": "Samplefrequentie"
		},

		"hks": [
			[
				"diversen",
				["ESC", "Sluit verschillende dingen"],

				"bestand beheer",
				["G", "Verwissel tussen list / grid weergave"],
				["T", "Verwissel tussen miniaturen / iconen"],
				["⇧ A/D", "Thumbnail formaat"],
				["ctrl-K", "Verwijder geselecteerde"],
				["ctrl-X", "Knip selectie naar klembord"],
				["ctrl-C", "Kopieer selectie naar klembord"],
				["ctrl-V", "Hier plakken (verplaatsen/kopieëren)"],
				["Y", "Download geselecteerde"],
				["F2", "Hernoem geselecteerde"],

				"bestand-lijst-selectie",
				["space", "wissel bestand selectie"],
				["↑/↓", "verplaats selectie cursor"],
				["ctrl ↑/↓", "verplaats cursor en scherm"],
				["⇧ ↑/↓", "select vorige/volgende bestand"],
				["ctrl-A", "selecteer alle bestanden / mappen"],
			], [
				"navigatie",
				["B", "verwissel breadcrumbs / navpane"],
				["I/K", "Vorige/volgende map"],
				["M", "Bovenliggende map (of huidige uitvouwen)"],
				["V", "Berwissel map / tekstbestand in navpane"],
				["A/D", "Navpane formaat"],
			], [
				"muziek-speler",
				["J/L", "Vorige/volgende song"],
				["U/O", "Skip 10sec terug/vooruit"],
				["0..9", "Spring naar 0%..90%"],
				["P", "Speel/pauzeer (start ook)"],
				["S", "Selecteer afspelende song"],
				["Y", "Download song"],
			], [
				"afbeelding viewer",
				["J/L, ←/→", "Vorige/volgende afbeelding"],
				["Home/End", "Eerste/laatste afbeelding"],
				["F", "Volledig scherm"],
				["R", "Draai rechtsom"],
				["⇧ R", "Draai linksom"],
				["S", "Selecteer afbeelding"],
				["Y", "Download afbeelding"],
			], [
				"video-speler",
				["U/O", "Skip 10sec terug/vooruit"],
				["P/K/Space", "Speel/pauze"],
				["C", "Verder met volgende"],
				["V", "herhaal"],
				["M", "stil"],
				["[ and ]", "zet herhaal interval"],
			], [
				"tekstbestand-viewer",
				["I/K", "vorige/volgende bestand"],
				["M", "sluit tekst bestand"],
				["E", "bewerk tekst bestand"],
				["S", "selecteer bestand (voor knip/kopie/hernoem)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Annuleren",

		"enable": "Inschakelen",
		"danger": "GEVAARLIJK",
		"clipped": "Gekopieërd naar klembord",

		"ht_s1": "seconde",
		"ht_s2": "secondes",
		"ht_m1": "minuut",
		"ht_m2": "minuten",
		"ht_h1": "uur",
		"ht_h2": "uur",
		"ht_d1": "dag",
		"ht_d2": "dagen",
		"ht_and": " en ",

		"goh": "Beheer-paneel",
		"gop": 'Vorige map">Vorige',
		"gou": 'Bovenligende map">Omhoog',
		"gon": 'Volgende map">Volgende',
		"logout": "Uitloggen ",
		"login": "Inloggen", //m
		"access": " Toegang",
		"ot_close": "Sluit onder-menu",
		"ot_search": "Zoek voor bestanden bij attributes, pad / naam, muziek tags, of elk andere combinatie tussen$N$N&lt;code&gt;foo bar&lt;/code&gt; = moet beide «foo» en «bar» bevatten,$N&lt;code&gt;foo -bar&lt;/code&gt; = moet «foo» bevatten maar geen «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = start met «yana» en moet een «opus» bestand zijn$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = moet precies «try unite» bevatten$N$Nde datum formaat is iso-8601, zoals$N&lt;code&gt;2009-12-31&lt;/code&gt; of &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: verwijder je recente uploads, of onvoltooide uploads afbreken",
		"ot_bup": "bup: Basisuploader, supports zelfs netscape 4.0",
		"ot_mkdir": "mkdir: Maak een nieuwe map",
		"ot_md": "new-md: Maak een nieuwe markdown bestand",
		"ot_msg": "msg: Verstuur een bericht naar de server logs",
		"ot_mp": "Media speler opties",
		"ot_cfg": "Configuratie opties",
		"ot_u2i": 'up2k: upload bestanden (als je schrijf toegang hebt) of verwissel naar zoek-mode om te zien of ze ergens bestaan op de server$N$Nuploads zijn hervatbaar, multithreaded, en bestandstijdstempels blijven behouden, maar het gebruikt meer CPU dan [🎈]&nbsp; (de basic uploader)<br /><br />tijdens het uploaden, dit icoon word dan een progress indicatie!',
		"ot_u2w": 'up2k: upload bestanden met hervattings ondersteuning (sluit je webbrowser en selecteer dezelfde bestand later opnieuw)$N$Nmultithreaded, en bestandstijdstempels blijven behouden, maar het gebruikt meer CPU dan [🎈]&nbsp; (de basic uploader)<br /><br />tijdens het uploaden, dit icoon word dan een progress indicatie!',
		"ot_noie": 'Gebruik alstublieft Chrome / Firefox / Edge',

		"ab_mkdir": "maak map",
		"ab_mkdoc": "nieuw markdown doc",
		"ab_msg": "verstuur msg naar srv log",

		"ay_path": "skip naar mappen",
		"ay_files": "skip naar bestanden",

		"wt_ren": "Hernoem geselecteerde items$NHotkey: F2",
		"wt_del": "Berwijder geselecteerde items$NHotkey: ctrl-K",
		"wt_cut": "Knip geselecteerde items &lt;small&gt;(en plak het ergens anders)&lt;/small&gt;$NHotkey: ctrl-X",
		"wt_cpy": "Kopieer geselecteerde items naar klembord$N(om te plakken ergens anders)$NHotkey: ctrl-C",
		"wt_pst": "Plak eeen laatst geknipte / gekopieërde selectie$NHotkey: ctrl-V",
		"wt_selall": "Selecteer alle bestanden$NHotkey: ctrl-A (wanneer bestand gefocused is)",
		"wt_selinv": "Selectie omkeren",
		"wt_zip1": "Download deze map als archief",
		"wt_selzip": "Download selectie als archief",
		"wt_seldl": "Download selectie als losse bestanden$NHotkey: Y",
		"wt_npirc": "Kopieer irc-geformarteerde track info",
		"wt_nptxt": "Kopieer platte tekst track info",
		"wt_m3ua": "Aan m3u afspeellijst toevoegen (klik <code>📻kopieer</code> later)",
		"wt_m3uc": "Kopieer m3u playlist naar klembord",
		"wt_grid": "Verwissel grid / lijst weergave$NHotkey: G",
		"wt_prev": "Vorig nummer$NHotkey: J",
		"wt_play": "Afspelen / pauzeer$NHotkey: P",
		"wt_next": "Volgend nummer$NHotkey: L",

		"ul_par": "Parallel uploads:",
		"ut_rand": "Willekeurige bestandsnaam",
		"ut_u2ts": "Kopieer de laatste-gewijzigde tijdstamp$Nvan je bestandsysteem naar de server\">📅",
		"ut_ow": "Overschrijf bestaande bestanden op de server?$N🛡️: nooit (zal in plaats daarvan een nieuwe bestandsnaam genereren)$N🕒: overschrijven als de server-bestand ouder is dan het geüploade bestand$N♻️: altijd overschrijven als de bestanden verschillend zijn",
		"ut_mt": "Ga door met hashen van andere bestanden tijdens het uploaden$N$Moet je misschien uitschakelen als je CPU of HDD het niet aan kan",
		"ut_ask": 'Vraag voor bevestiging voordat het uploaden start">💭',
		"ut_pot": "Verbeter de uploadsnelheid voor langzame apparaten$Ndoor de interface minder complex te maken",
		"ut_srch": "Niet uploaden, maar check of de bestanden als op de server bestaan$N (checkt alle mappen die waar jij toegang op hebt)",
		"ut_par": "Pauzeer bij zetten het op 0$N$Nverhoog als je verbinding traag is$N$Nhou het op 1 als je netwerk of server HDD het niet aankan",
		"ul_btn": "Drop bestanden / mappen<br>hier (of klik mij)",
		"ul_btnu": "U P L O A D",
		"ul_btns": "Z O E K E N",

		"ul_hash": "Hashing",
		"ul_send": "Versturen",
		"ul_done": "Klaar",
		"ul_idle1": "Geen uploads in wachtrij",
		"ut_etah": "Gemiddelde &lt;em&gt;hashing&lt;/em&gt; snelheid en geschatte tijd tot de voltooiing",
		"ut_etau": "Gemiddelde &lt;em&gt;verzend&lt;/em&gt; snelheid en geschatte tijd tot voltooiing",
		"ut_etat": "Gemiddelde &lt;em&gt;totale&lt;/em&gt; snelheid en geschatte tijd tot voltooiing",

		"uct_ok": "Succesvol afgerond",
		"uct_ng": "Niet goed: gefaald / geweigerd / niet gevonden",
		"uct_done": "ok en ng gecombineerd",
		"uct_bz": "Hashing van uploads",
		"uct_q": "Inactief, in afwachting",

		"utl_name": "Bestandsnaam",
		"utl_ulist": "Lijst",
		"utl_ucopy": "Kopieer",
		"utl_links": "Links",
		"utl_stat": "Status",
		"utl_prog": "Vooruitgang",

		// keep short:
		"utl_404": "404",
		"utl_err": "FOUT",
		"utl_oserr": "OS-FOUT",
		"utl_found": "gevonden",
		"utl_defer": "Uitgesteld",
		"utl_yolo": "YOLO",
		"utl_done": "klaar",

		"ul_flagblk": "De bestanden zijn toegevoegd aan de wachtrij</b><br>maar er is een drukke up2k bezig in een andere tabblad,<br>wachten totdat die eerst klaar is",
		"ul_btnlk": "De server configuratie heeft deze schakelaar versleuteld in deze staat",

		"udt_up": "Upload",
		"udt_srch": "Zoeken",
		"udt_drop": "Laat hier los",

		"u_nav_m": '<h6>Hey, wat heb jij daar?</h6><code>Enter</code> = Bestanden (een of meer)\n<code>ESC</code> = Een map (inclusief submappen)',
		"u_nav_b": '<a href="#" id="modal-ok">Bestanden</a><a href="#" id="modal-ng">Een map</a>',

		"cl_opts": "Switches",
		"cl_themes": "Thema",
		"cl_langs": "Taal",
		"cl_ziptype": "Download map als",
		"cl_uopts": "up2k switches",
		"cl_favico": "Favicon",
		"cl_bigdir": "Item limiet in map",
		"cl_hsort": "#sorteer",
		"cl_keytype": "Key notaties",
		"cl_hiddenc": "Verborgen kolomen",
		"cl_hidec": "Verborgen",
		"cl_reset": "Reset",
		"cl_hpick": "Tik op de kolomkoppen om ze in de onderstaande tabel te verbergen",
		"cl_hcancel": "Kolumn verbergen geannuleerd",

		"ct_grid": '田 grid',
		"ct_ttips": '◔ ◡ ◔">ℹ️ tooltips',
		"ct_thumb": 'In grid-overzicht, wissel tussen iconen of thumbnails$NHotkey: T">🖼️ thumbs',
		"ct_csel": 'Gebruik CTRL en SHIFT voor de bestand selectie in grid-overzicht>sel',
		"ct_ihop": 'Als je afbeeldingviewer afsluit, scroll omlaag naar de laatst bekeken bestand">g⮯',
		"ct_dots": 'Laat verborgen bestanden zien (als de server dat toestaat)">dotfiles',
		"ct_qdel": 'Waneeer je een bestand verwijderd, vraag eenmalig om bevestiging">qdel',
		"ct_dir1st": 'Sorteer mappen eerst en dan de bestanden">📁 first',
		"ct_nsort": 'Natural sort (voor bestandsnamen dat beginnen met getallen)">nsort',
		"ct_readme": 'Laat README.md in mappen lijst zien">📜 readme',
		"ct_utc": 'Toon alle datums en tijden in UTC">UTC',
		"ct_idxh": 'Laat index.html zien in plaats van de map overzicht">htm',
		"ct_sbars": 'Laat scrollbars zien">⟊',

		"cut_umod": "Als een bestand al bestaat op de server, update de 'gewijzigd' waarde op het bestand wat op de server staat met het bestand wat je geupload hebt (vereist schrijf+verwijder rechten)\">re📅",

		"cut_turbo": "De yolo knop, die wil jij waarschijnlijk NIET actief wilt hebben:$N$Ngebruik dit als je heel veel bestanden gaat uploaden EN je moest het herstarten voor een reden en je wilt doorgaan met uploaden ASAP$N$Ndit vervangt de hash-check met een simpele <em>&quot;heeft dit dezelfde bestands groote op de server?&quot;</em>, zo als de bestands inhoud verschillend is, dan worden ze NIET geupload$N$NJe zou deze optie weer uit moeten zetten als de upload klaar is en dan &quot;upload&quot; de zelfde bestanden opnieuw uploaden zo de client het kan verifieren\">turbo",

		"cut_datechk": "Heeft geen effect tenzij de turbo knop actief is$N$Nverminder de yolo factor (een klein beetje); controlleert of de bestand tijdstamp op de server hetzelfde is met het geuploade bestand$N$Ndit zou <em>in theorie</em> de meest onvoltooide/onvoledige uploads, maar dit is geen vervaning voor de verificatie-check met de turbo knop uitgeschakeld daarna\">date-chk",

		"cut_u2sz": "Grote (in MiB) voor elk geuploade stuk; grote waardes vliegen beter over de Atlantische Oceaan. Probeer lage waardes op zeer onstabiele verbindingen",

		"cut_flag": "Alleen een tabblad kan bestanden uploaden $N -- andere tabbladen moeten deze optie ook actief hebben $N -- dit heeft alleen effect op de tabbladen die op hetzelfde domain zijn",

		"cut_az": "Bestanden uploaden in alfabetische volgorde, in plaats van kleinste bestanden eerst$N$Nalfabetische volgorde kan het makkelijker maken om te zien of er wat fout is gegaan op de server, dit maakt het uploaden ietsjes trager op fiber / LAN",

		"cut_nag": "Systeem notificatie weergeven als een upload voltooid is$N(alleen als de browser of tabblad niet actief is)",
		"cut_sfx": "Geluid waarschuwing afspelen als een upload voltooid is$N(alleen als de browser of tabblad niet actief is)",

		"cut_mt": "Gebruik multithreading om bestands-hashing te versnellen$N$Ndit gebruikt web-workers en vereist$Nmeer geheugen (tot wel 512 MiB extra)$N$Nmaakt https 30% sneller en http 4.5x sneller\">mt",

		"cut_wasm": "Gebruik wasm in plaats van de webbrowser ingebouwde hasher; verbetert de snelheid op chrome-gebaseerde webbrowsers maar verhoogd CPU gebruik, veel oude versie van chrome hebben een bug dat een geheugen lek heeft, dat kan alle geheugen in gebruik nemen en crashen als dit actief is\">wasm",

		"cft_text": "Favicon tekst (laat leeg en vernieuw om uit te schakelen)",
		"cft_fg": "Voorgrondkleur",
		"cft_bg": "Achtergrondkleur",

		"cdt_lim": "Max aantal bestanden laten zien in een map",
		"cdt_ask": "Als helemaal naar beneden gescrolld bent,$Nin plaats van meer inladen,$Nvraag wat het moet doen",
		"cdt_hsort": "Hoeveel sorteerregels (&lt;code&gt;,sorthref&lt;/code&gt;) moeten er in media-URL's worden opgenomen? Als je dit op 0 instelt, worden de sorteerregels in medialinks ook genegeerd wanneer erop geklikt word.",

		"tt_entree": "Laat navpane zien (directoryboom zijbalk)$NHotkey: B",
		"tt_detree": "Laat breadcrumbs zien$NHotkey: B",
		"tt_visdir": "Scroll naar geselecteerde map",
		"tt_ftree": "Verwissel tussen directoryboom / tekst bestanden$NHotkey: V",
		"tt_pdock": "Laat bovenliggende mappen zien in een vastgezet deelvenster bovenaan",
		"tt_dynt": "Automatisch groeien naarmate de directoryboom zich uitbreidt",
		"tt_wrap": "Automatische terugloop",
		"tt_hover": "Laat overlopenden lijnen zien bij zweven$N(stopt het scrollen tenzij de muis in de linker gedeelte van het scherm is)",

		"ml_pmode": "Aan het einde van de map...",
		"ml_btns": "Cmds",
		"ml_tcode": "Transcode",
		"ml_tcode2": "Transcode naar",
		"ml_tint": "Tint",
		"ml_eq": "Audio-equalizer",
		"ml_drc": "Dynamisch bereikcompressor",

		"mt_loop": "Loop/herhaal een nummer\">🔁",
		"mt_one": "Stop na een nummer\">1️⃣",
		"mt_shuf": "Shuffle alle muziek in alle mappen\">🔀",
		"mt_aplay": "Autoplay als er een song-ID staat in de link waarop je hebt geklikt om naar de server te gaan$N$NAls u dit uitschakelt, wordt de pagina-URL ook niet meer bijgewerkt met nummer-ID's tijdens het afspelen van muziek. Dit voorkomt automatisch afspelen als deze instellingen verloren gaan, maar de URL behouden blijft.\">a▶",
		"mt_preload": "Begin het laden van de volgende nummer vlak voordat de huidige nummer het einde bereikt voor gapless playback\">preload",
		"mt_prescan": "Ga naar de volgende map voordat de laatste nummer eindigd$NMaakt de webbrower blij$NZo het afspelen van muziek niet gestopt word\">nav",
		"mt_fullpre": "Probeer het hele nummer vooraf te laden;$N✅ activeer dit op <b>onstabiele</b> verbindingen,$N❌ <b>zet uit</b> als je waarschijnlijk een trage verbinding hebt\">full",
		"mt_fau": "Op telefoons, voorkom muziek van stoppen als de volgende nummer niet snel genoeg voorgeladen is (kan de weergave van tags glitchy maken)\">☕️",
		"mt_waves": "Waveform zoekbar:$NToon audio-amplitude in de zoekbar\">~s",
		"mt_npclip": "Knoppen tonen voor het clipboarden van het nummer dat op dat moment wordt afgespeeld\">/np",
		"mt_m3u_c": "Knoppen tonen om de geselecteerde nummers als m3u8-afspeellijstitems te clipboarden\">📻",
		"mt_octl": "OS-integratie (media hotkeys / osd)\">os-ctl",
		"mt_oseek": "Zoeken via os-integratie mogelijk maken$N$NNotitie: op sommige toestellen (iPhones) dit vervcangt de volgende-nummer knop\">seek",
		"mt_oscv": "Albumhoes weergeven in osd\">art",
		"mt_follow": "Het afgespeelde nummer in beeld houden\">🎯",
		"mt_compact": "Compacte bedieningselementen\">⟎",
		"mt_uncache": "Cache wissen &nbsp;(Probeer dit als uw browser een kapotte kopie van een nummer heeft gecached, waardoor het niet afgespeeld kan worden)\">uncache",
		"mt_mloop": "De open map herhalen\">🔁 loop",
		"mt_mnext": "Laad de volgende map en ga verder\">📂 next",
		"mt_mstop": "Stoppen met afspelen\">⏸ stop",
		"mt_cflac": "flac / wav omzetten naar {0}\">flac",
		"mt_caac": "aac / m4a omzetten naar {0}\">aac",
		"mt_coth": "Alle andere bestanden (geen mp3) converteren naar {0}\">oth",
		"mt_c2opus": "Beste keuze voor computers, laptops, android\">opus",
		"mt_c2owa": "opus-weba, voor iOS 17.5 en nieuwer\">owa",
		"mt_c2caf": "opus-caf, voor iOS 11 tot en met iOS 17\">caf",
		"mt_c2mp3": "Gebruik dit hele oude toestellen\">mp3",
		"mt_c2flac": "Beste geluidskwaliteit, maar grote downloads\">flac", //m
		"mt_c2wav": "Ongemprimeerde weergave (nog groter)\">wav", //m
		"mt_c2ok": "Mooi, goede keuze",
		"mt_c2nd": "Dat is niet het aanbevolen uitvoerformaat voor uw apparaat, maar dat is prima",
		"mt_c2ng": "Uw apparaat lijkt dit uitvoerformaat niet te ondersteunen, maar we gaan het toch proberen",
		"mt_xowa": "iOS bevat bugs waardoor dit formaat niet op de achtergrond kan worden afgespeeld; gebruik in plaats daarvan caf of mp3.",
		"mt_tint": "Achtergrond helderheid (0-100) op de zoekbalk om bufferen minder storend te maken",
		"mt_eq": "Schakelt de equalizer en gain-control in;$N$Nboost &lt;code&gt;0&lt;/code&gt; = standaard 100% volume (ongeweijzigd)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = standaard stereo (ongeweijzigd)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% links-rechts crossfeed$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = stemverwijdering :^)$N$NDoor de equalizer in te schakelen, worden gapless albums volledig gapless. Laat hem dus aanstaan met alle waarden op nul (behalve width = 1) als je dat belangrijk vindt.",
		"mt_drc": "Schakelt de dynamic range compressor in (volume flattener / brickwaller); schakelt ook EQ in om de spaghetti te balanceren, dus zet alle EQ velden behalve ‘width’ op 0 als je dat niet wilt.$N$Nverlaagt het volume van audio boven THRESHOLD dB; voor elke RATIO dB voorbij THRESHOLD is er 1 dB output, dus standaardwaarden van tresh -24 en ratio 12 betekenen dat het nooit luider dan -22 dB zou moeten worden en het is veilig om de equalizer boost te verhogen tot 0.8, of zelfs 1.8 met ATK 0 en een enorme RLS zoals 90 (werkt alleen in firefox; RLS is max 1 in andere browsers)$N$N(zie wikipedia, die legt het veel beter uit)",

		"mb_play": "Afspelen",
		"mm_hashplay": "Deze audio bestand afspelen?",
		"mm_m3u": "Druk op <code>Enter/OK</code> om af te spelen\nDruk op <code>ESC/Annuleren</code> om te bewerken",
		"mp_breq": "Heeft firefox 82+ of chrome 73+ of iOS 15+",
		"mm_bload": "Aan het laden...",
		"mm_bconv": "Opmzetten naar {0}, even geduld...",
		"mm_opusen": "Uw browser kan geen aac / m4a-bestanden afspelen;\ntranscodering naar opus is nu ingeschakeld",
		"mm_playerr": "Afspelen mislukt: ",
		"mm_eabrt": "De afspeelpoging is geannuleerd",
		"mm_enet": "Je internetverbinding is onstabiel",
		"mm_edec": "Dit bestand is vermoedelijk beschadigd??",
		"mm_esupp": "Uw browser begrijpt deze audio-formaat niet",
		"mm_eunk": "Onbekende fout",
		"mm_e404": "Kan audio niet afspelen; fout 404: Bestand niet gevonden..",
		"mm_e403": "Kan audio niet afspelen; fout 403: Toegang geweigerd.\n\nProbeer op F5 te drukken om opnieuw te laden, misschien ben je uitgelogd",
		"mm_e500": "Kan geen audio afspelen; fout 500: Controleer serverlogs.",
		"mm_e5xx": "Kan geen audio afspelen; serverfout ",
		"mm_nof": "Geen audiobestanden meer vinden in de buurt",
		"mm_prescan": "Op zoek naar muziek om als volgende te spelen...",
		"mm_scank": "Het volgende nummer gevonden:",
		"mm_uncache": "Cache gewist; alle nummers worden opnieuw gedownload bij de volgende keer afspelen",
		"mm_hnf": "Dat liedje bestaat niet meer",

		"im_hnf": "Deze afbeelding bestaat niet meer",

		"f_empty": 'Deze map is leeg',
		"f_chide": 'Dit verbergt kolom «{0}»\n\nje kunt kolommen verbergen op de instellingen tabblad',
		"f_bigtxt": "Dit bestand is {0} MiB groot -- echt bekijken als tekst?",
		"f_bigtxt2": "Wilt u alleen het einde van het bestand bekijken? Dit maakt ook volgen/tailen mogelijk, waarbij nieuw toegevoegde tekstregels in realtime worden weergegeven.",
		"fbd_more": '<div id="blazy"><code>{0}</code> van de <code>{1}</code> bestanden weergegeven; <a href="#" id="bd_more">Toon {2}</a> of <a href="#" id="bd_all">Laat alles zien</a></div>',
		"fbd_all": '<div id="blazy"><code>{0}</code> van de <code>{1}</code> bestanden weergegeven; <a href="#" id="bd_all">Laat alles zien</a></div>',
		"f_anota": "Alleen {0} van de {1} items zijn geselecteerd;\nom de volledige map te selecteren, scrol je eerst naar beneden",

		"f_dls": 'de bestandslinks in de huidige map zijn veranderd in downloadlinks',

		"f_partial": "Om een bestand dat momenteel wordt geüpload veilig te downloaden, klikt u op het bestand met dezelfde bestandsnaam, maar zonder de bestandsextensie <code>.PARTIAL</code>. Druk op Annuleren of Escape om dit te doen.\n\nAls u op OK / Enter drukt, wordt deze waarschuwing genegeerd en gaat u verder met het downloaden van het gedeeltelijke <code>.PARTIAL</code> scratchbestand, waardoor u vrijwel zeker beschadigde gegevens krijgt.",

		"ft_paste": "plakken {0} items$NHotkey: ctrl-V",
		"fr_eperm": 'kan de naam niet wijzigen:\nje hebt geen “move” rechten in deze map',
		"fd_eperm": 'kan niet verwijderen:\nje hebt geen “delete” rechten in deze map',
		"fc_eperm": 'kan niet knippen:\nje hebt geen “move” rechten in deze map',
		"fp_eperm": 'kan niet plakken:\nje hebt geen “schrijf” rechten in deze map',
		"fr_emore": "selecteer ten minste één item om te hernoemen",
		"fd_emore": "selecteer minstens één item om te verwijderen",
		"fc_emore": "selecteer ten minste één item om te knippen",
		"fcp_emore": "selecteer ten minste één item om naar het klembord te kopiëren",

		"fs_sc": "Deel de map waarin je je bevindt",
		"fs_ss": "De geselecteerde bestand(en) delen",
		"fs_just1d": "U kunt niet meer dan één map selecteren\nof mix bestanden en mappen in één selectie",
		"fs_abrt": "❌ Afbreken",
		"fs_rand": "🎲 rand.naam",
		"fs_go": "✅ Maak share",
		"fs_name": "Naam",
		"fs_src": "Bron",
		"fs_pwd": "Wachtwoord",
		"fs_exp": "Verloopt",
		"fs_tmin": "min",
		"fs_thrs": "uur",
		"fs_tdays": "dag(en)",
		"fs_never": "eeuwig",
		"fs_pname": "Optionele linknaam; is willekeurig als deze leeg is",
		"fs_tsrc": "Het bestand of de map die u wilt delen",
		"fs_ppwd": "Optioneel wachtwoord",
		"fs_w8": "Delen...",
		"fs_ok": "Druk op <code>Enter/OK</code> naar klembord te zetten\Druk op <code>ESC/Annuleren</code> om te sluiten",

		"frt_dec": "Kan sommige gevallen van gebroken bestandsnamen oplossen\">url-decode",
		"frt_rst": "Gewijzigde bestandsnamen terugzetten naar de oorspronkelijke namen\">↺ reset",
		"frt_abrt": "Afbreken en dit venster sluiten\">❌ Annuleren",
		"frb_apply": "HERNOEMEN TOEPASSEN",
		"fr_adv": "Batch / metadata / patroon hernoemen\">Geavanceerd",
		"fr_case": "Hoofdlettergevoelige regex\">case",
		"fr_win": "Windows-veilige namen; vervangen <code>&lt;&gt;:&quot;\\|?*</code> met japanse tekens over de volledige breedte\">win",
		"fr_slash": "Vervang <code>/</code> met een teken waardoor er geen nieuwe mappen worden gemaakt\">geen /",
		"fr_re": "Regex zoekpatroon om toe te passen op originele bestandsnamen; naar capturing groups kan worden verwezen in het onderstaande opmaakveld zoals &lt;code&gt;(1)&lt;/code&gt; en &lt;code&gt;(2)&lt;/code&gt; enzovoort",
		"fr_fmt": "Geïnspireerd door foobar2000 :$N&lt;code&gt;(titel)&lt;/code&gt; wordt vervangen door de titel van het nummer,$N&lt;code&gt;[(artiest) - ](titel)&lt;/code&gt; sla [dit] gedeelte over als artiest leeg is$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; vult tracknummer op tot 2 cijfers (0X)",
		"fr_pdel": "Verwijderen",
		"fr_pnew": "Opslaan als",
		"fr_pname": "Geef een naam op voor je nieuwe preset",
		"fr_aborted": "Afgebroken",
		"fr_lold": "Oude naam",
		"fr_lnew": "Nieuwe naam",
		"fr_tags": "Tags voor de geselecteerde bestanden (alleen-lezen, alleen ter referentie):",
		"fr_busy": "Hernoemen van {0} items...\n\n{1}",
		"fr_efail": "Hernoemen mislukt:\n",
		"fr_nchg": "{0} van de nieuwe namen zijn gewijzigd als gevolg van <cod>win</code> en/of <code>geen /</code>\n\nOK om door te gaan met deze gewijzigde nieuwe namen?",

		"fd_ok": "Verwijderen OK",
		"fd_err": "Verwijderen mislukt:\n",
		"fd_none": "Er is niets verwijderd; misschien geblokkeerd door serverconfiguratie (xbd)?",
		"fd_busy": "{0} items verwijderen...\n\n{1}",
		"fd_warn1": "VERWIJDER deze {0} items?",
		"fd_warn2": "<b>LAATSTE KANS!</b> Geen manier om ongedaan te maken. Verwijderen?",

		"fc_ok": "Knip {0} items",
		"fc_warn": 'Knip {0} items\n\nmaar: alleen <b>deze</b> browser-tabblad kan weer plakken\n(omdat de selectie zo enorm is)',

		"fcc_ok": "{0} items naar klembord gekopieerd",
		"fcc_warn": '{0} items naar klembord gekopieerd\n\maar: alleen <b>deze</b> browser-tabblad kan weer plakken\n(omdat de selectie zo enorm is)',

		"fp_apply": "Gebruik deze namen",
		"fp_ecut": "Knip of kopieer eerst enkele bestanden/mappen om te verplaatsen/plakken\n\nnotitie: je kunt knippen/plakken in verschillende browsertabbladen",
		"fp_ename": "{0} items kunnen hier niet worden verplaatst omdat de namen al in gebruik zijn. Geef ze hieronder een nieuwe naam om verder te gaan, of verwijder de naam om ze over te slaan:",
		"fcp_ename": "{0} items kunnen hier niet worden gekopieerd omdat de namen al in gebruik zijn. Geef ze hieronder een nieuwe naam om verder te gaan, of verwijder de naam om ze over te slaan:",
		"fp_emore": "Er zijn nog enkele bestandsnaambotsingen die moeten worden opgelost",
		"fp_ok": "Verplaatsen OK",
		"fcp_ok": "Kopiëren OK",
		"fp_busy": "{0} items verplaatsen...\n\n{1}",
		"fcp_busy": "{0} items kopiëren...\n\n{1}",
		"fp_abrt": "afbreken...", //m
		"fp_err": "Verplaatsen mislukt:\n",
		"fcp_err": "Kopieëren mislukt:\n",
		"fp_confirm": "Verplaats deze {0} items hierheen?",
		"fcp_confirm": "Kopieer deze {0} items hier?",
		"fp_etab": 'Kan klembord van ander browsertabblad niet lezen',
		"fp_name": "Een bestand uploaden vanaf uw apparaat. Geef het een naam:",
		"fp_both_m": '<h6>Kies wat je wilt plakken</h6><code>Enter</code> = Verplaatsen {0} bestanden van «{1}»\n<code>ESC</code> = Upload {2} bestanden van je apparaat',
		"fcp_both_m": '<h6>Kies wat je wilt plakken</h6><code>Enter</code> = Kopieer {0} bestanden van «{1}»\n<code>ESC</code> = Upload {2} bestanden van je apparaat',
		"fp_both_b": '<a href="#" id="modal-ok">Verplaats</a><a href="#" id="modal-ng">Upload</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopieer</a><a href="#" id="modal-ng">Upload</a>',

		"mk_noname": "Voer een naam in het tekstveld aan de linkerkant voordat je verder gaat :p",

		"tv_load": "Tekstdocument laden:\n\n{0}\n\n{1}% ({2} van de {3} MiB geladen)",
		"tv_xe1": "Kon tekstbestand niet laden:\n\nfout ",
		"tv_xe2": "404, bestand niet gevonden",
		"tv_lst": "Lijst met tekstbestanden in",
		"tvt_close": "Terugkeren naar mapweergave$NHotkey: M (of Esc)\">❌ Sluiten",
		"tvt_dl": "Download dit bestand$NHotkey: Y\">💾 download",
		"tvt_prev": "Vorig document tonen$NHotkey: i\">⬆ prev",
		"tvt_next": "Volgende document tonen$NHotkey: K\">⬇ next",
		"tvt_sel": "Selecteer bestand &nbsp; ( voor knip / verplaats / verwijder / ... )$NHotkey: S\">sel",
		"tvt_edit": "Bestand openen in teksteditor$NHotkey: E\">✏️ bewerk",
		"tvt_tail": "Bestand controleren op wijzigingen; nieuwe regels in realtime weergeven\">📡 volgen",
		"tvt_wrap": "Automatische terugloop\">↵",
		"tvt_atail": "Vergrendelen scroll naar onderkant van pagina\">⚓",
		"tvt_ctail": "Kleuren van terminals decoderen (ansi escape codes)\">🌈",
		"tvt_ntail": "Terugrollimiet (hoeveel tekst geladen moeten blijven)",

		"m3u_add1": "Nummer toegevoegd aan m3u afspeellijst",
		"m3u_addn": "{0} nummers toegevoegd aan m3u-afspeellijst",
		"m3u_clip": "m3u-afspeellijst nu gekopieerd naar klembord\n\nje moet een nieuw tekstbestand maken met de naam iets.m3u en de afspeellijst in dat document plakken; dit maakt het afspeelbaar",

		"gt_vau": "Laat geen video's zien, speel alleen de audio af\">🎧",
		"gt_msel": "Schakel bestandsselectie in; ctrl-klik op een bestand om te openen$N$N&lt;em&gt;indien actief: dubbelklik op een bestand / map om het te openen&lt;/em&gt;$N$NHotkey: S\">multiselect",
		"gt_crop": "Gecentreerde miniaturen\">crop",
		"gt_3x": "Hi-res miniaturen\">3x",
		"gt_zoom": "Zoom",
		"gt_chop": "Verkorten",
		"gt_sort": "Sorteer bij",
		"gt_name": "naam",
		"gt_sz": "grootte",
		"gt_ts": "datum",
		"gt_ext": "type",
		"gt_c1": "Bestandsnamen meer inkorten (minder tonen)",
		"gt_c2": "Bestandsnamen minder inkorten (meer tonen)",

		"sm_w8": "Zoeken...",
		"sm_prev": "Onderstaande zoekresultaten zijn afkomstig van een eerdere zoekopdracht:\n  ",
		"sl_close": "Zoekresultaten sluiten",
		"sl_hits": "Toont {0} treffers",
		"sl_moar": "Laad meer",

		"s_sz": "grootte",
		"s_dt": "datum",
		"s_rd": "pad",
		"s_fn": "naam",
		"s_ta": "tags",
		"s_ua": "op@",
		"s_ad": "adv.",
		"s_s1": "Minimaal MiB",
		"s_s2": "Maximaal MiB",
		"s_d1": "Min. iso8601",
		"s_d2": "Max. iso8601",
		"s_u1": "Uploaded na",
		"s_u2": "en/of voor",
		"s_r1": "Pad bevad &nbsp; (spatie-gescheiden)",
		"s_f1": "Naam bevat &nbsp; (ontkennen met -nope)",
		"s_t1": "Tags bevat &nbsp; (^=start, einde=$)",
		"s_a1": "Specifieke metadata-eigenschappen",

		"md_eshow": "Kan niet weergeven ",
		"md_off": "[📜<em>readme</em>] uitgeschakeld in [⚙️] -- document verborgen",

		"badreply": "Mislukt om antwoord van server te parsen",

		"xhr403": "403: Toegang geweigerd\n\nprobeer F5 in te drukken, misschien ben je uitgelogd",
		"xhr0": "Onbekend (waarschijnlijk verbinding met server verloren of server is offline)",
		"cf_ok": "Sorry daarvoor -- DD" + wah + "OS-bescherming ingeschakeld\n\nalles zou binnen ongeveer 30 seconden moeten hervatten\n\nals er niets gebeurt, druk dan op F5 om de pagina opnieuw te laden",
		"tl_xe1": "Kon submappen niet weergeven:\n\nfout ",
		"tl_xe2": "404: Map niet gevonden",
		"fl_xe1": "Kon bestanden in map niet weergeven:\n\nfout ",
		"fl_xe2": "404: Map niet gevonden",
		"fd_xe1": "Kon submap niet aanmaken:\n\nfout ",
		"fd_xe2": "404: Bovenliggende map niet gevonden",
		"fsm_xe1": "Kon bericht niet verzenden:\n\nfout ",
		"fsm_xe2": "404: Bovenliggende map niet gevonden",
		"fu_xe1": "Mislukt om unpost lijst van server te laden:\n\nfout ",
		"fu_xe2": "404: Bestand niet gevonden??",

		"fz_tar": "gnu-tar bestand uitpakken (linux / mac)",
		"fz_pax": "pax-formaat tar uitpakken (trager)",
		"fz_targz": "gnu-tar met gzip niveau 3 compressie$N$Ndit is meestal erg langzaam, dus gebruik in plaats daarvan ongecomprimeerde tar",
		"fz_tarxz": "gnu-tar met xz-niveau 1 compressie$N$Ndit is meestal erg langzaam, dus gebruik in plaats daarvan ongecomprimeerde tar",
		"fz_zip8": "Zip met utf8 bestandsnamen (misschien onhandig op windows 7 en ouder)",
		"fz_zipd": "Zip met traditionele cp437-bestandsnamen, voor echt oude software",
		"fz_zipc": "cp437 met crc32 vroeg berekend$Nvoor MS-DOS PKZIP v2.04g (oktober 1993)$N(het duurt langer voordat het downloaden kan beginnen)",

		"un_m1": "Hieronder kunt u uw recente uploads verwijderen (of onvoltooide uploads afbreken)",
		"un_upd": "Vernieuwen",
		"un_m4": "of deel de bestanden die hieronder zichtbaar zijn:",
		"un_ulist": "Toon",
		"un_ucopy": "Kopieer",
		"un_flt": "Optionele filter:&nbsp; URL moet het volgende bevatten",
		"un_fclr": "Reset filter",
		"un_derr": 'unpost-verwijderen mislukt:\n',
		"un_f5": 'Er is iets kapot, probeer te verversen of druk op F5',
		"un_uf5": "Sorry, maar u moet de pagina vernieuwen (bijvoorbeeld door op F5 of CTRL-R te drukken) voordat deze upload kan worden afgebroken.",
		"un_nou": '<b>Waarschuwing:</b> server te druk om onvoltooide uploads weer te geven; klik straks op de "refresh" link',
		"un_noc": '<b>Waarschuwing:</b> unpost van volledig geüploade bestanden is niet ingeschakeld/toegestaan in de serverconfiguratie',
		"un_max": "Toont de eerste 2000 bestanden (gebruik de filter)",
		"un_avail": "{0} recente uploads kunnen worden verwijderd<br />{1} onvoltooide kunnen worden afgebroken",
		"un_m2": "Gesorteerd op uploadtijd; meest recente eerst:",
		"un_no1": "sike! geen enkele upload is recent genoeg",
		"un_no2": "sike! geen uploads die aan dat filter voldoen zijn voldoende recent",
		"un_next": "Verwijder de volgende {0} bestanden",
		"un_abrt": "Afbreken",
		"un_del": "Verwijderen",
		"un_m3": "Je recente uploads laden...",
		"un_busy": "Verwijderen van {0} bestanden...",
		"un_clip": "{0} links gekopieerd naar klembord",

		"u_https1": "Je moet",
		"u_https2": "overschakelen naar https",
		"u_https3": "voor betere prestaties",
		"u_ancient": 'Je browser is indrukwekkend oud -- misschien moet je <a href="#" onclick="goto(\'bup\')">in plaats daarvan bup gebruiken</a>',
		"u_nowork": "Je moet firefox 53+ of chrome 57+ of iOS 11+ hebben",
		"tail_2old": "Je moet firefox 105+ of chrome 71+ of iOS 14.5+ hebben",
		"u_nodrop": 'Je browser is te oud voor uploaden via slepen en neerzetten',
		"u_notdir": "Dat is geen map!\n\nuw browser is te oud,\nprobeer in plaats daarvan sleep en neerzetten",
		"u_uri": "Om afbeeldingen te slepen vanuit andere browser tabblad,\nplaats deze dan op de grote uploadknop",
		"u_enpot": 'Overschakelen naar <a href="#">potato UI</a> (kan uploadsnelheid verbeteren)',
		"u_depot": 'Overschakelen naar <a href="#">fancy UI</a> (kan uploadsnelheid verminderen)',
		"u_gotpot": 'Overschakelen naar de potato UI voor verbeterde uploadsnelheid,\n\nVoel je vrij om het er niet mee eens te zijn en schakel terug!',
		"u_pott": "<p>Bestanden: &nbsp; <b>{0}</b> klaar, &nbsp; <b>{1}</b> mislukt, &nbsp; <b>{2}</b> bezig, &nbsp; <b>{3}</b> in de wachtrij</p>",
		"u_ever": "Dit is de basis uploader; up2k heeft minstens het volgende nodig<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'Dit is de basis uploader; <a href="#" id="u2yea">up2k</a> is beter',
		"u_uput": 'Optimaliseren voor snelheid (checksum overslaan)',
		"u_ewrite": 'Je hebt geen schrijftoegang tot deze map',
		"u_eread": 'Je hebt geen leestoegang tot deze map',
		"u_enoi": 'Zoeken naar bestanden is niet ingeschakeld in de serverconfiguratie',
		"u_enoow": "Overschrijven zal hier niet werken; je heb verwijder toestemming nodig",
		"u_badf": 'Deze {0} bestanden (van {1} totaal) zijn overgeslagen, mogelijk door bestandssysteemmachtigingen:\n\n',
		"u_blankf": 'Deze {0} bestanden (van {1} totaal) zijn leeg; alsnog uploaden?\n\n',
		"u_applef": 'Deze {0} bestanden (van {1} totaal) zijn waarschijnlijk ongewenst;\nKlik op <code>OK/Enter</code> om de volgende bestanden over te slaan,\Klik op <code>Annuleren/ESC</code> niet uit te sluiten en deze ook te uploaden:\n\n',
		"u_just1": '\nMisschien werkt het beter als je slechts één bestand selecteert',
		"u_ff_many": "Als je <b>Linux / MacOS / Android,</b> gebruikt dan <em>kan</em> deze hoeveelheid bestanden <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\">Firefox crashen!</a>\nals dat gebeurt, probeer het dan opnieuw (of gebruik Chrome).",
		"u_up_life": "Deze upload wordt verwijderd van de server\n{0} nadat het is voltooid",
		"u_asku": 'Upload deze {0} bestanden naar <code>{1}</code>',
		"u_unpt": "Je kunt deze upload ongedaan maken / verwijderen met de linkerbovenhoek 🧯",
		"u_bigtab": 'We staan op het punt om {0} bestanden te tonen\n\nDit kan uw browser laten crashen, weet je het zeker??',
		"u_scan": 'Bestanden scannen...',
		"u_dirstuck": 'Directory iterator liep vast bij het benaderen van het volgende {0} items; zal het volgende overslaan:',
		"u_etadone": 'Klaar ({0}, {1} bestanden)',
		"u_etaprep": '(klaarmaken om te uploaden)',
		"u_hashdone": 'hashing klaar',
		"u_hashing": 'Hash',
		"u_hs": 'Hallo zeggen...',
		"u_started": "De bestanden worden nu geüpload; zie [🚀]",
		"u_dupdefer": "Duplicaat; wordt verwerkt na alle andere bestanden",
		"u_actx": "klik op deze tekst om prestatieverlies</br>bij het overschakelen naar andere vensters/tabbladen te voorkomen",
		"u_fixed": "OK!&nbsp; Fixed it 👍",
		"u_cuerr": "Mislukt bij het uploaden van stuk {0} van {1};\nwaarschijnlijk ongevaarlijk, doorgaan\n\nbestand: {2}",
		"u_cuerr2": "Upload door server geweigerd (stuk {0} van {1});\nzal later opnieuw proberen\n\nbestand: {2}\n\nfout ",
		"u_ehstmp": "Zal opnieuw proberen; zie rechtsonder",
		"u_ehsfin": "Server heeft het verzoek om de upload te finaliseren afgewezen; opnieuw proberen...",
		"u_ehssrch": "Server heeft de zoekaanvraag afgewezen; opnieuw proberen...",
		"u_ehsinit": "Server heeft het verzoek om het uploaden te starten afgewezen; opnieuw proberen...",
		"u_eneths": "Netwerkfout tijdens het uitvoeren van de uploadhanddruk; opnieuw proberen...",
		"u_enethd": "Netwerkfout tijdens het testen van het bestaan van het doel; opnieuw proberen...",
		"u_cbusy": "Wachten tot de server ons weer vertrouwt na een netwerkstoring...",
		"u_ehsdf": "Server heeft geen schijfruimte meer!\n\nzal blijven proberen, voor het geval iemand genoeg ruimte vrijmaakt om door te gaan",
		"u_emtleak1": "Het lijkt erop dat uw webbrowser een geheugenlek heeft;\nprobeer",
		"u_emtleak2": ' <a href="{0}">over te schakel over naar https (aanbevolen)</a> of ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'Probeer het volgende:\n<ul><li>druk op <code>F5</code> om de pagina te verversen</li><li>dan schakel de &nbsp;<code>mt</code>&nbsp; uit, deze knop staat in &nbsp;<code>⚙️ instellingen</code></li><li>en probeer de upload opnieuw</li></ul>Uploaden zal wat langzamer gaan, maar ja.\nSorry voor de problemen!\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">heeft een bugfix</a> voor dit',
		"u_emtleakf": '{robeer het volgende:\n<ul><li>druk op <code>F5</code> om de pagina te verversen</li><li>dan activeer <code>🥔</code> (aardappel) in de upload scherm<li>en probeer de upload opnieuw</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">heeft mogelijk een fix</a> op een gegeven moment',
		"u_s404": "Niet gevonden op server",
		"u_expl": "Leg uit",
		"u_maxconn": "De meeste browsers beperken dit tot 6, maar firefox laat je dit verhogen met <code>network.http.max-persistent-connections-per-server</code> in <code>about:config</code>",
		"u_tu": '<p class="warn">WAARSCHUWING: turbo ingeschakeld, <span>&nbsp;webbrowser detecteert en hervat onvolledige uploads mogelijk niet; zie de tooltip van de turboknop</span></p>',
		"u_ts": '<p class="warn">WAARSCHUWING: turbo ingeschakeld, <span>&nbsp;zoekresultaten kunnen onjuist zijn; zie turbo-knop tooltip</span></p>',
		"u_turbo_c": "Turbo is uitgeschakeld in serverconfiguratie",
		"u_turbo_g": "Turbo uitgeschakeld, je geen recht om mappen in deze volume te tonen",
		"u_life_cfg": 'Automatisch verwijderen na <input id="lifem" p="60" /> minuten (of <input id="lifeh" p="3600" /> uur)',
		"u_life_est": 'Upload wordt verwijderd <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'Deze map dwingt een\nmaximale levensduur van {0} af',
		"u_unp_ok": 'unpost is toegestaan voor {0}',
		"u_unp_ng": 'unpost zijn NIET toegestaan',
		"ue_ro": 'Je toegang tot deze map is alleen-lezen\n\n',
		"ue_nl": 'Je bent momenteel niet ingelogd',
		"ue_la": 'Je bent momenteel aangemeld als "{0}"',
		"ue_sr": 'U bevindt zich momenteel in de bestandszoekmodus\n\nschakel over naar uploadmodus door op het vergrootglas te klikken 🔎 (naast de grote ZOEK-knop), en probeer opnieuw te uploaden\n\nsorry',
		"ue_ta": 'Probeer opnieuw te uploaden, het zou nu moeten werken',
		"ue_ab": "Dit bestand wordt al geüpload naar een andere map en die upload moet worden voltooid voordat het bestand naar een andere map kan worden geüpload.\n\nU kunt de eerste upload afbreken en laten vergeten met de linkerbovenhoek 🧯",
		"ur_1uo": "OK: Bestand succesvol geüpload",
		"ur_auo": "OK: Alle {0} bestanden succesvol geüpload",
		"ur_1so": "OK: Bestand gevonden op server",
		"ur_aso": "OK: Alle {0} bestanden gevonden op server",
		"ur_1un": "Uploaden mislukt, sorry",
		"ur_aun": "Alle {0} uploads mislukt, sorry",
		"ur_1sn": "Bestand NIET gevonden op server",
		"ur_asn": "De {0} bestanden zijn NIET gevonden op de server",
		"ur_um": "Voltooid;\n{0} upload(s) OK,\n{1} upload(s) mislukt, sorry",
		"ur_sm": "Voltooid;\n{0} bestand(en) gevonden op de server,\n{1} bestand(en) NIET gevonden op de server",

		"lang_set": "Vernieuw de pagina om de wijziging door te voeren?",
	},
	"nno": {
		"tt": "Nynorsk",

		"cols": {
			"c": "handlingsknappar",
			"dur": "varigheit",
			"q": "kvalitet / bitrate",
			"Ac": "lydformat",
			"Vc": "videoformat",
			"Fmt": "format / innpakning",
			"Ahash": "lydkontrollsum",
			"Vhash": "videokontrollsum",
			"Res": "oppløysing",
			"T": "filtype",
			"aq": "lydkvalitet / bitrate",
			"vq": "videokvalitet / bitrate",
			"pixfmt": "fargekoding / detaljnivå",
			"resw": "horisontal oppløysing",
			"resh": "vertikal oppløysing",
			"chs": "lydkanaler",
			"hz": "lydoppløsing"
		},

		"hks": [
			[
				"ymse",
				["ESC", "lukk saker og ting"],

				"filbehandlar",
				["G", "listevisning eller ikon"],
				["T", "miniatyrbilder på/av"],
				["⇧ A/D", "ikonstorleik"],
				["ctrl-K", "slett valde"],
				["ctrl-X", "klipp ut valde"],
				["ctrl-C", "kopiér åt utklippstavle"],
				["ctrl-V", "lim inn (flytt/kopiér)"],
				["Y", "last ned valde"],
				["F2", "endre namn på valde"],

				"filmarkering",
				["space", "markér fil"],
				["↑/↓", "flytt markør"],
				["ctrl ↑/↓", "flytt markør og scroll"],
				["⇧ ↑/↓", "velg forr./neste fil"],
				["ctrl-A", "velg alle filer / mapper"],
			], [
				"navigering",
				["B", "mappehierarki eller filsti"],
				["I/K", "forr./neste mappe"],
				["M", "eitt nivå opp (eller lukk)"],
				["V", "vis mapper eller tekstfiler"],
				["A/D", "panelstorleik"],
			], [
				"musikkspelar",
				["J/L", "forr./neste song"],
				["U/O", "hopp 10sek bak/fram"],
				["0..9", "hopp åt 0%..90%"],
				["P", "pause, eller start / fortsett"],
				["S", "marker spelande song"],
				["Y", "last ned song"],
			], [
				"bildevisar",
				["J/L, ←/→", "forr./neste bilde"],
				["Home/End", "første/siste bilde"],
				["F", "fullskjermvisning"],
				["R", "rotér åt høyre"],
				["⇧ R", "rotér åt venstre"],
				["S", "markér bilde"],
				["Y", "last ned bilde"],
			], [
				"videospelar",
				["U/O", "hopp 10sek bak/fram"],
				["P/K/Space", "pause / fortsett"],
				["C", "fortsett åt neste fil"],
				["V", "gjenta avspeling"],
				["M", "lyd av/på"],
				["[ og ]", "gjentaksintervall"],
			], [
				"dokumentvisar",
				["I/K", "forr./neste fil"],
				["M", "lukk tekstdokument"],
				["E", "redigér tekstdokument"],
				["S", "markér fil (for F2/ctrl-x/...)"],
				["Y", "last ned tekstfil"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Avbryt",

		"enable": "Aktiv",
		"danger": "VARSKU",
		"clipped": "kopiert åt utklippstavla",

		"ht_s1": "sekund",
		"ht_s2": "sekund",
		"ht_m1": "minutt",
		"ht_m2": "minutt",
		"ht_h1": "time",
		"ht_h2": "timar",
		"ht_d1": "dag",
		"ht_d2": "dagar",
		"ht_and": " og ",

		"goh": "kontrollpanel",
		"gop": 'navigér åt mappa før den her">forr.',
		"gou": 'navigér eitt nivå opp">opp',
		"gon": 'navigér åt mappa etter den her">neste',
		"logout": "Logg ut ",
		"login": "Logg inn",
		"access": " åtgang",
		"ot_close": "lukk reiskap",
		"ot_search": "søk etter filer ved å angje filnamn, mappenamn, tid, storleik, eller metadata som songtittel / artist / osv.$N$N&lt;code&gt;foo bar&lt;/code&gt; = inneheld båe «foo» og «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = innehold «foo» men ikkje «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = startar med «yana», filtype «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = «try unite» eksakt$N$Ndatoformat er iso-8601, så f.eks.$N&lt;code&gt;2009-12-31&lt;/code&gt; eller &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: slett filer som du nyleg har lastet opp; «angre-knappen»",
		"ot_bup": "bup: tradisjonell / primitiv filopplasting,$N$Nfungerar i om lag samtlege nettlesarar",
		"ot_mkdir": "mkdir: lag ei ny mappe",
		"ot_md": "new-md: lag eit nytt markdown-dokument",
		"ot_msg": "msg: send ein beskjed åt serverloggen",
		"ot_mp": "musikkspelarinstillinger",
		"ot_cfg": "andre innstillinger",
		"ot_u2i": 'up2k: last opp filer (viss du har skriveåtgang) eller bytt åt søkemodus for å sjekke om filene finnast ein eller annan plass på serveren$N$Nopplastinger kan startast opp att etter avbrot, skjer stykkevis for potensielt høgare ytelse, og ivaretek datostempling -- men bruker litt meir prosessorkraft enn [🎈]&nbsp; (den primitive opplastaren "bup")<br /><br />mens opplastinger føregår så visast framdrifta her oppe!',
		"ot_u2w": 'up2k: filopplasting med støtte for å starte opp att avbrotne opplastinger -- steng ned nettlesaren og drage dei same filene inn i nettlesaren igjen for å plukke opp att der du slapp$N$Nopplastinger skjer stykkevis for potensielt høgare ytelse, og ivaretek datostempling -- men bruker litt meir prosessorkraft enn [🎈]&nbsp; (den primitive opplastaren "bup")<br /><br />mens opplastinger føregår så visast framdrifta her oppe!',
		"ot_noie": 'Fungerer mye betre i Chrome / Firefox / Edge',

		"ab_mkdir": "lag mappe",
		"ab_mkdoc": "nytt dokument",
		"ab_msg": "send melding",

		"ay_path": "gå videre åt mapper",
		"ay_files": "gå videre åt filer",

		"wt_ren": "gje nye namn åt dei valde filene$NSnarvei: F2",
		"wt_del": "slett dei valde filene$NSnarvei: ctrl-K",
		"wt_cut": "klipp ut dei valde filene &lt;small&gt;(for å lime inn ein annan plass)&lt;/small&gt;$NSnarvei: ctrl-X",
		"wt_cpy": "kopiér dei valde filene åt utklippstavla$N(for å lime inn ein annan plass)$NSnarvei: ctrl-C",
		"wt_pst": "lim inn filer (som tidligare blei klipt ut / kopiert ein annan plass)$NSnarvei: ctrl-V",
		"wt_selall": "velg alle filer$NSnarvei: ctrl-A (mens fokus er på ei fil)",
		"wt_selinv": "invertér utval",
		"wt_zip1": "last ned denne mappa som eit arkiv",
		"wt_selzip": "last ned dei valde filene som eit arkiv",
		"wt_seldl": "last ned dei valde filene$NSnarvei: Y",
		"wt_npirc": "kopiér songinfo (irc-formatert)",
		"wt_nptxt": "kopiér songinfo",
		"wt_m3ua": "legg song åt i m3u-speleliste$N(husk å klikk på <code>📻copy</code> senere)",
		"wt_m3uc": "kopiér m3u-spelelista åt utklippstavla",
		"wt_grid": "bytt mellom ikon og listevising$NSnarvei: G",
		"wt_prev": "førre  song$NSnarvei: J",
		"wt_play": "play / pause$NSnarvei: P",
		"wt_next": "neste song$NSnarvei: L",

		"ul_par": "samtidige handl.:",
		"ut_rand": "finn opp nye tilfeldige filnamn",
		"ut_u2ts": "gje fila på serveren same$Ntidsstempel som lokalt hos deg\">📅",
		"ut_ow": "overskrive eksisterande filer på serveren?$N🛡️: aldri (finn på eit nytt filnamn i staden for)$N🕒: overskriv viss fila åt serveren er eldre$N♻️: alltid, gitt at innholdet er annleis",
		"ut_mt": "fortsett å synfare køa mens opplasting føregår$N$Nskru denne av dersom du har ein$Ntreig prosessor eller harddisk",
		"ut_ask": 'bekreft filutvalg før opplasting startar">💭',
		"ut_pot": "forbetre ytinga på treige einheiter ved å$Nforenkle brukergrensesnittet",
		"ut_srch": "gjer eit søk i staden for å laste opp --$Nleitar gjennom alle mappane du har lov åt å sjå",
		"ut_par": "sett åt 0 for å midlertidig stoppe opplasting$N$Nhøge verdier (4 eller 8) kan gje betre yting,$Nspesielt på treige internettlinjer$N$Nbør ikkje vere høgare enn 1 på LAN$Neller viss serveren sin harddisk er treig",
		"ul_btn": "slepp filer / mapper<br>her (eller klikk meg)",
		"ul_btnu": "L A S T &nbsp; O P P",
		"ul_btns": "F I L S Ø K",

		"ul_hash": "synfar",
		"ul_send": "&nbsp;send",
		"ul_done": "total",
		"ul_idle1": "ingen handlinger i køen",
		"ut_etah": "snitthastigheit for &lt;em&gt;synfaring&lt;/em&gt; samt gjenståande tid",
		"ut_etau": "snitthastigheit for &lt;em&gt;opplasting&lt;/em&gt; samt gjenståande tid",
		"ut_etat": "&lt;em&gt;total&lt;/em&gt; snitthastigheit og gjenståande tid",

		"uct_ok": "fullført uten problem",
		"uct_ng": "fullført under tvil (duplikat, ikkje funne, ...)",
		"uct_done": "fullført (enten &lt;em&gt;ok&lt;/em&gt; eller &lt;em&gt;ng&lt;/em&gt;)",
		"uct_bz": "aktive handlinger (synfaring / opplasting)",
		"uct_q": "køa",

		"utl_name": "filnamn",
		"utl_ulist": "vis",
		"utl_ucopy": "kopiér",
		"utl_links": "lenker",
		"utl_stat": "status",
		"utl_prog": "fremdrift",

		// må vere korte:
		"utl_404": "404",
		"utl_err": "FEIL!",
		"utl_oserr": "OS-feil",
		"utl_found": "funnet",
		"utl_defer": "seinare",
		"utl_yolo": "YOLO",
		"utl_done": "ferdig",

		"ul_flagblk": "filene har blitt lagd i køa</b><br>men det er ein anna nettlesarfane som held på med synfaring eller opplasting akkurat no,<br>så venter åt den er ferdig først",
		"ul_btnlk": "brytaren har blitt låst åt denne tilstanden i serverens konfigurasjon",

		"udt_up": "Last opp",
		"udt_srch": "Søk",
		"udt_drop": "Slepp filene her",

		"u_nav_m": '<h6>kva har du?</h6><code>Enter</code> = Filer (éin eller fleire)\n<code>ESC</code> = Éi mappe (inkludert undermapper)',
		"u_nav_b": '<a href="#" id="modal-ok">Filer</a><a href="#" id="modal-ng">Éi mappe</a>',

		"cl_opts": "brytarar",
		"cl_themes": "utsjånad",
		"cl_langs": "språk",
		"cl_ziptype": "nedlasting av mapper",
		"cl_uopts": "up2k-brytarar",
		"cl_favico": "favicon",
		"cl_bigdir": "store mapper",
		"cl_hsort": "#sort",
		"cl_keytype": "notasjon for musikalsk dur",
		"cl_hiddenc": "skjulte kolonner",
		"cl_hidec": "skjul",
		"cl_reset": "nullstill",
		"cl_hpick": "klikk på overskrifta åt kolonnene du ønskjer å skjule i tabellen nedanfor",
		"cl_hcancel": "kolonne-skjuling avbrote",

		"ct_grid": '田 ikon',
		"ct_ttips": 'vis hjelpetekst ved å holde musa over ting">ℹ️ tips',
		"ct_thumb": 'vis miniatyrbilder i staden for ikon$NSnarvei: T">🖼️ bilder',
		"ct_csel": 'bruk tastane CTRL og SHIFT for markering av filer i ikonvising">merk',
		"ct_ihop": 'bla ned åt sist viste bilde når bildevisaren lukkast">g⮯',
		"ct_dots": 'vis skjulte filer (gitt at serveren tillèt det)">.synlig',
		"ct_qdel": 'sletteknappen spør berre éin gong om stadfesting">hurtig🗑️',
		"ct_dir1st": 'sortér slik at mapper kjem framanfor filer">📁 først',
		"ct_nsort": 'naturlig sortering (skjønar tal i filnamn)">nsort',
		"ct_utc": 'bruk UTC for alle klokkeslett">UTC',
		"ct_readme": 'vis README.md nedanfor filene">📜 readme',
		"ct_idxh": 'vis index.html i staden for filliste">htm',
		"ct_sbars": 'vis rullgardiner / skrollefelt">⟊',

		"cut_umod": 'i tilfelle ei fil du lastar opp alt finnast på serveren, så skal tidsstempelet åt serveren oppdaterast slik at det stemmer overeins med din lokale fil (krev rettigheitene write+delete)">re📅',

		"cut_turbo": "forenkla synfaring ved opplasting; bør etter alt å døme <em>ikkje</em> skruast på:$N$Nnyttig dersom du var midt i ei svær opplasting som måtte startast på nytt av ein eller annan grunn, og du vil komme i gang igjen så raskt som i det heile mulig.$N$Nnår denne er skrudd på så forenklast synfaringa kraftig; i staden for å utføre ein trygg sjekk på om filene finnast på serveren i god stand, så sjekkast det kun om <em>filstorleiken</em> stemmer. Så dersom ein korrupt fil vere på serveren allerede, på same plass, med same storleik og namn, så blir det <em>ikkje oppdaga</em>.$N$Ndet anbefalast å kun benytte denne funksjonen for å komme seg raskt gjennom sjølve opplastinga, for så å skru den av, og åt slutt &quot;laste opp&quot; dei same filene éin gong åt -- slik at integriteten kan verifiserast\">turbo",

		"cut_datechk": "har ingen effekt dersom turbo er skrudd av$N$Ngjer turbo bittelitt tryggare ved å sjekke datostemplinga på filene (i tillegg åt filstorleik)$N$N<em>burde</em> oppdage og gjenoppta dei fleste ufullstendige opplastinger, men er <em>ikkje</em> ein fullverdig erstatning for å deaktivere turbo og gjere ein skikkeleg sjekk\">date-chk",

		"cut_u2sz": "storleik i megabyte for kvart bruddstykke for opplasting. Store verdiar flyg betre over atlanteren. Små verdiar kan vere betre på flettande ustabile samband",

		"cut_flag": "samkøyrer nettlesarfaner slik at berre éin $N kan holde på med synfaring / opplasting $N -- andre faner må óg ha denne skrudd på $N -- fungerar kun innanom same domene",

		"cut_az": "last opp filer i alfabetisk rekkefølge, i staden for minste-fil-først$N$Nalfabetisk kan gjere det lettare å anslå om alt gjekk bra, men er bittelitt treigare på fiber / LAN",

		"cut_nag": "meldingsvarsel når opplasting er ferdig$N(kun om nettlesarfana ikkje er synlig)",
		"cut_sfx": "lydvarsel når opplasting er ferdig$N(kun om nettlesarfanen ikkje er synlig)",

		"cut_mt": "raskere synfaring ved å bruke heile CPU'en$N$Ndenne funksjonen nytter web-workers$Nog krev meir RAM (opptil 512 MiB ekstra)$N$Ngjer https 30% raskare, http 4.5x raskare\">mt",

		"cut_wasm": "bruk wasm i staden for nettlesaren sin sha512-funksjon; gjev betre yting på chrome-baserte nettlesarar, men brukar meir CPU, og eldre versjoner av chrome toler det ikkje (et opp all RAM og kræsjer)\">wasm",

		"cft_text": "ikontekst (blank ut og last siden på nytt for å deaktivere)",
		"cft_fg": "farge",
		"cft_bg": "bakgrunnsfarge",

		"cdt_lim": "maks mengd filer å vise per mappe",
		"cdt_ask": "vis knappar for å laste fleire filer nederst på sida i staden for å gradvis laste meir av mappea når man scroller ned",
		"cdt_hsort": "antall sorteringsreglar (&lt;code&gt;,sorthref&lt;/code&gt;) som skal inkluderast når media-URL'ar genererast. Dersom denne er 0 så vil sorteringsreglar i URL'ar korkje bli generert eller lest",

		"tt_entree": "bytt åt mappehierarki$NSnarvei: B",
		"tt_detree": "bytt åt tradisjonell stivising$NSnarvei: B",
		"tt_visdir": "bla ned åt den åpne mappa",
		"tt_ftree": "bytt mellom filstruktur og tekstfiler$NSnarvei: V",
		"tt_pdock": "vis dei overordna mappane i eit panel",
		"tt_dynt": "øk bredda på panelet ettersom treet utvider seg",
		"tt_wrap": "linjebryting",
		"tt_hover": "vis heile mappenamnet når musepeikaren treff mappa$N( gjer diverre at scrollhjulet fusker dersom musepeikaren ikkje finn seg i grøfta )",

		"ml_pmode": "ved enden av mappa",
		"ml_btns": "knapper",
		"ml_tcode": "konvertering",
		"ml_tcode2": "konvertér til",
		"ml_tint": "tint",
		"ml_eq": "audio equalizer (tonejustering)",
		"ml_drc": "compressor (volumutjevning)",

		"mt_loop": "spel den same songen om og om igjen\">🔁",
		"mt_one": "spel kun éin song\">1️⃣",
		"mt_shuf": "songane i kvar mappe$Nspelast i tilfeldig rekkefølge\">🔀",
		"mt_aplay": "prøv å starte avspeling viss linken du trykte på for å åpne nettsida inneheld ein song-ID$N$Nviss denne deaktiverast så vil heller ikkje nettside-URL'en bli oppdatert med song-ID'er når musikk spelast, i tilfelle innstillingane skulle gå tapt og nettsida lastast på ny\">a▶",
		"mt_preload": "hent ned litt av neste song i forkant,$Nslik at pausa i overgangen blir mindre\">forsyn",
		"mt_prescan": "ved behov, bla åt neste mappe$Nslik at nettlesaren lar oss$Nfortsetja å spele musikk\">bla",
		"mt_fullpre": "hent ned heile neste song, ikkje berre litt:$N✅ skru på viss nettet ditt er <b>ustabilt</b>,$N❌ skru av viss nettet ditt er <b>treigt</b>\">full",
		"mt_fau": "for telefoner: forhindre at avspeling stoppar viss nettet er for treigt åt å laste neste song i tide. Viss påskrudd kan det forårsake at songinfo ikkje visast korrekt i OS'et\">☕️",
		"mt_waves": "waveform seekbar:$Nvis volumkurve i avspelingsfeltet\">~s",
		"mt_npclip": "vis knappar for å kopiere info om songen du høyrer på\">/np",
		"mt_m3u_c": "vis knapper for å kopiere dei valde$Nsongene som innslag i ei m3u8-speleliste\">📻",
		"mt_octl": "integrering med operativsystemet (fjernkontroll, infoskjerm)\">os-ctl",
		"mt_oseek": "gje løyve åt spoling med fjernkontroll$N$Nmerk: på nokon eininger (iPhones) så vil$Ndette erstatte knappen for neste song\">spoling",
		"mt_oscv": "vis albumcover på infoskjermen\">bilde",
		"mt_follow": "bla slik at songen som spelast alltid er synleg\">🎯",
		"mt_compact": "tettpakka spelarpanel\">⟎",
		"mt_uncache": "prøv denne viss ein song ikkje spelar riktig\">oppfrisk",
		"mt_mloop": "repetér heile mappa\">🔁 gjenta",
		"mt_mnext": "hopp åt neste mappe og fortsett\">📂 neste",
		"mt_mstop": "stopp avspeling\">⏸ stopp",
		"mt_cflac": "konvertér flac / wav-filer åt {0}\">flac",
		"mt_caac": "konvertér aac / m4a-filer åt to {0}\">aac",
		"mt_coth": "konvertér alt anna (men ikkje mp3) åt {0}\">andre",
		"mt_c2opus": "det beste valget for alle PCar og Android\">opus",
		"mt_c2owa": "opus-weba, for iOS 17.5 og nyare\">owa",
		"mt_c2caf": "opus-caf, for iOS 11 åt og med 17\">caf",
		"mt_c2mp3": "bra valg for steinalder-utstyr (slår aldri feil)\">mp3",
		"mt_c2flac": "gir best lydkvalitet, men et nettet ditt\">flac",
		"mt_c2wav": "heilt rå lydstrøm (bruker enda meir data enn flac)\">wav",
		"mt_c2ok": "bra valg!",
		"mt_c2nd": "ikkje det føretrekte valget for din einheit, men funker sikkert greit",
		"mt_c2ng": "ser verkelig ikkje ut som enheiten din taklar dette formatet... men ok, vi prøver",
		"mt_xowa": "iOS har fortsatt problem med avspeling av owa-musikk i bakgrunnen. Bruk caf eller mp3 i staden for",
		"mt_tint": "nivå av bakgrunnsfarge på søkestripa (0-100),$Ngjer oppdateringer mindre distraherande",
		"mt_eq": "aktivér tonekontroll og forsterker;$N$Nboost &lt;code&gt;0&lt;/code&gt; = normal volumskala$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = normal stereo$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% blanding venstre-høgre$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = instrumental :^)$N$Nreduserer óg daudtid mellom songfiler",
		"mt_drc": "aktivér volum-utjevning (dynamic range compressor); vil óg aktivere tonejustering, så sett alle EQ-feltene bortsett frå 'width' åt 0 viss du ikkje vil ha nokon EQ$N$Nfilteret vil dempe volumet på alt som er høgare enn TRESH dB; for kvar RATIO dB over grensa er det 1dB som treff høgtalarane, så standardverdiane tresh -24 og ratio 12 skal bety at volumet ikkje gjeng høgare enn -22 dB, slik at ein trygt kan øke boost-verdien i equalizeren åt rundt 0.8, eller 1.8 kombinert med ATK 0 og RLS 90 (berre mulig i firefox; andre nettlesarar tek ikkje høgare RLS enn 1)$N$Nwikipedia forklarar dette mykje betre forresten",

		"mb_play": "lytt",
		"mm_hashplay": "spel denne songen?",
		"mm_m3u": "trykk <code>Enter/OK</code> for å spele\ntrykk <code>ESC/Avbryt</code> for å redigere",
		"mp_breq": "krev firefox 82+, chrome 73+, eller iOS 15+",
		"mm_bload": "lastar inn...",
		"mm_bconv": "konverterer åt {0}, vent litt...",
		"mm_opusen": "nettlesaren din skjønar ikkje aac / m4a;\nkonvertering åt opus er no aktivert",
		"mm_playerr": "avspeling feilet: ",
		"mm_eabrt": "Avspelingsforespørselen blei avbroten",
		"mm_enet": "Nettet ditt er ustabilt",
		"mm_edec": "Noko er galt med musikkfila",
		"mm_esupp": "Nettleseren din skjønar ikkje filtypen",
		"mm_eunk": "Ukjent feil",
		"mm_e404": "Avspeling feilet: Fil ikkje funnet.",
		"mm_e403": "Avspeling feilet: Høve nekta.\n\nKanskje du blei logget ut?\nPrøv å trykk F5 for å laste sida på nytt.",
		"mm_e500": "Avspeling feilet: Rusk i maskineriet, sjekk serverloggen.",
		"mm_e5xx": "Avspeling feilet: ",
		"mm_nof": "finn ikkje flere songer i nærheita",
		"mm_prescan": "Leitar etter neste song...",
		"mm_scank": "Fann neste song:",
		"mm_uncache": "alle songer vil lastast på nytt ved neste avspeling",
		"mm_hnf": "songen finnast ikkje lenger",

		"im_hnf": "bildet finnast ikkje lenger",

		"f_empty": 'denne mappa er tom',
		"f_chide": 'dette vil skjule kolonna «{0}»\n\nfana for "andre innstillinger" let deg vise kolonna igjen',
		"f_bigtxt": "denne fila er heeile {0} MiB -- vis som tekst?",
		"f_bigtxt2": "vil du sjå bunnen av filen i staden for? du vil da óg sjå nye linjer som blir lagd åt på slutten av filen i sanntid",
		"fbd_more": '<div id="blazy">visar <code>{0}</code> av <code>{1}</code> filer; <a href="#" id="bd_more">vis {2}</a> eller <a href="#" id="bd_all">vis alle</a></div>',
		"fbd_all": '<div id="blazy">visar <code>{0}</code> av <code>{1}</code> filer; <a href="#" id="bd_all">vis alle</a></div>',
		"f_anota": "kun {0} av totalt {1} element blei markert;\nfor å velje alt må du bla åt bunnen av mappa først",

		"f_dls": 'lenkane i denne mappa er no\nomgjort åt nedlastingsknappar',

		"f_partial": "For å laste ned ei fil som enda ikkje er ferdig opplasta, klikk på filen som har same filnamn som denne, men uten <code>.PARTIAL</code> på slutten. Da vil serveren passe på at nedlastinga går bra. Derfor anbefalast det sterkt å trykkje AVBRYT eller Escape-tasten.\n\nViss du verkelig ønskjer å laste ned denne <code>.PARTIAL</code>-filen på ein ukontrollert måte, trykk OK / Enter for å ignorere denne advarselen. Slik vil du høgst sannsynleg motta korrupt data.",

		"ft_paste": "Lim inn {0} filer$NSnarvei: ctrl-V",
		"fr_eperm": 'kan ikkje endre namn:\ndu har ikkje høve åt “move” i denne mappa',
		"fd_eperm": 'kan ikkje slette:\ndu har ikkje høve åt “delete” i denne mappa',
		"fc_eperm": 'kan ikkje klippe ut:\ndu har ikkje høve åt “move” i denne mappa',
		"fp_eperm": 'kan ikkje lime inn:\ndu har ikkje høve åt “write” i denne mappa',
		"fr_emore": "vel minst éi fil som skal få nytt namn",
		"fd_emore": "vel minst éi fil som skal slettast",
		"fc_emore": "vel minst éi fil som skal klippast ut",
		"fcp_emore": "vel minst éi fil som skal kopierast åt utklippstavla",

		"fs_sc": "del mappa du er i no",
		"fs_ss": "del dei valde filene",
		"fs_just1d": "du kan ikkje markere flere mapper samtidig,\neller kombinere mapper og filer",
		"fs_abrt": "❌ avbryt",
		"fs_rand": "🎲 tilfeldig namn",
		"fs_go": "✅ opprett deling",
		"fs_name": "namn",
		"fs_src": "kjelde",
		"fs_pwd": "passord",
		"fs_exp": "varigheit",
		"fs_tmin": "min",
		"fs_thrs": "timar",
		"fs_tdays": "dagar",
		"fs_never": "for evig",
		"fs_pname": "valfri namn (blir litt tilfeldig ellers)",
		"fs_tsrc": "fil/mappe som skal delast",
		"fs_ppwd": "valfri passord",
		"fs_w8": "opprettar deling...",
		"fs_ok": "trykk <code>Enter/OK</code> for å kopiere lenka (for CTRL-V)\ntrykk <code>ESC/Avbryt</code> for å kun bekrefta",

		"frt_dec": "kan korrigere visse ødelagte filnamn\">url-decode",
		"frt_rst": "nullstillar endringar (tilbake åt dei originale filnamna)\">↺ reset",
		"frt_abrt": "avbryt og lukk dette vindauget\">❌ avbryt",
		"frb_apply": "IVERKSETT",
		"fr_adv": "automasjon basert på metadata<br>og / eller mønster (regulære uttrykk)\">avansert",
		"fr_case": "versalfølsomme uttrykk\">Aa",
		"fr_win": "bytt ut bokstavane <code>&lt;&gt;:&quot;\\|?*</code> med$Ntilsvarande som windows ikkje får panikk av\">win",
		"fr_slash": "bytt ut bokstaven <code>/</code> slik at den ikkje forårsakar at nye mapper opprettes\">ikke /",
		"fr_re": "regex-mønster som køyrast på kvart filnamn. Grupper kan leses ut i format-feltet nedanfor, f.eks. &lt;code&gt;(1)&lt;/code&gt; og &lt;code&gt;(2)&lt;/code&gt; osv.",
		"fr_fmt": "inspirert av foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; byttast ut med songtittel,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; dropper [dette] viss artist er blank$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; visar songnr. med 2 siffer",
		"fr_pdel": "slett",
		"fr_pnew": "lagre som",
		"fr_pname": "gje innstillingane dine eit namn",
		"fr_aborted": "avbrote",
		"fr_lold": "gamalt namn",
		"fr_lnew": "nytt namn",
		"fr_tags": "metadata for dei valde filene (kun for referanse):",
		"fr_busy": "endrar namn på {0} filer...\n\n{1}",
		"fr_efail": "endring av namn feila:\n",
		"fr_nchg": "{0} av namna blei justert pga. <code>win</code> og/eller <code>ikkje /</code>\n\nvil du fortsetja med dei nye namna som blei valde?",

		"fd_ok": "sletting OK",
		"fd_err": "sletting feila:\n",
		"fd_none": "ingenting blei sletta; kanskje avvist av serverkonfigurasjon (xbd)?",
		"fd_busy": "slettar {0} filer...\n\n{1}",
		"fd_warn1": "SLETT disse {0} filene?",
		"fd_warn2": "<b>Siste sjanse!</b> Dette kan ikkje angrast. Slett?",

		"fc_ok": "klipte ut {0} filer",
		"fc_warn": 'klipte ut {0} filer\n\nmen: kun <b>denne</b> nettlesarfana har muligheit åt å lime dei inn ein annan plass, siden antallet filer er helt hinsides',

		"fcc_ok": "kopierte {0} filer åt utklippstavla",
		"fcc_warn": 'kopierte {0} filer åt utklippstavla\n\nmen: kun <b>denne</b> nettlesarfana har muligheit åt å lime dei inn ein annan plass, sidan antallet filer er heilt på hi sida',

		"fp_apply": "bekreft og lim inn no",
		"fp_ecut": "du må klippe ut eller kopiere nokre filer / mapper først\n\nmerk: du kan gjerne jobbe på kryss av nettlesarfaner; klippe ut i éi fane, lime inn i ei anna",
		"fp_ename": "{0} filer kan ikkje flyttast åt målmappa fordi det allereie finnast filer med same namn. Gi dei nye namn nedanfor, eller gje dei eit blankt namn for å hoppe over dei:",
		"fcp_ename": "{0} filer kan ikkje kopierast åt målmappa fordi det allereie finnast filer med same namn. Gi dei nye namn nedanfor, eller gje dei eit blankt namn for å hoppe over dei:",
		"fp_emore": "det er fortsatt fleire namn som må endrast",
		"fp_ok": "flytting OK",
		"fcp_ok": "kopiering OK",
		"fp_busy": "flyttar {0} filer...\n\n{1}",
		"fcp_busy": "kopierar {0} filer...\n\n{1}",
		"fp_abrt": "avbryt...",
		"fp_err": "flytting feila:\n",
		"fcp_err": "kopiering feila:\n",
		"fp_confirm": "flytt disse {0} filene hit?",
		"fcp_confirm": "kopiér disse {0} filene hit?",
		"fp_etab": 'kunne ikkje lese lista med filer frå den andre nettlesarfana',
		"fp_name": "Lastar opp éi fil frå einheita di. Velg filnamn:",
		"fp_both_m": '<h6>kva skal limast inn her?</h6><code>Enter</code> = Flytt {0} filer frå «{1}»\n<code>ESC</code> = Last opp {2} filer frå einheita din',
		"fcp_both_m": '<h6>kva skal limes inn her?</h6><code>Enter</code> = Kopiér {0} filer frå «{1}»\n<code>ESC</code> = Last opp {2} filer frå einheita din',
		"fp_both_b": '<a href="#" id="modal-ok">Flytt</a><a href="#" id="modal-ng">Last opp</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopiér</a><a href="#" id="modal-ng">Last opp</a>',

		"mk_noname": "skriv inn eit namn i tekstboksa åt venstre først :p",

		"tv_load": "Lastar inn tekstfil:\n\n{0}\n\n{1}% ({2} av {3} MiB lasta ned)",
		"tv_xe1": "kunne ikkje laste tekstfil:\n\nfeil ",
		"tv_xe2": "404, Fil ikkje funne",
		"tv_lst": "tekstfiler i mappa",
		"tvt_close": "gå tilbake åt mappa$NSnarvei: M (eller Esc)\">❌ lukk",
		"tvt_dl": "last ned denne fila$NSnarvei: Y\">💾 last ned",
		"tvt_prev": "vis førre dokument$NSnarvei: i\">⬆ forr.",
		"tvt_next": "vis neste dokument$NSnarvei: K\">⬇ neste",
		"tvt_sel": "markér fila &nbsp; ( for utklipp / sletting / ... )$NSnarvei: S\">merk",
		"tvt_edit": "redigér fila$NSnarvei: E\">✏️ endre",
		"tvt_tail": "overvak fila for endringar og vis nye linjer i sanntid\">📡 følg",
		"tvt_wrap": "tekstbryting\">↵",
		"tvt_atail": "hald dei nyaste linjene synlege (lås åt botnen av sida)\">⚓",
		"tvt_ctail": "skjøn og vis terminalfargar (ansi-sekvensar)\">🌈",
		"tvt_ntail": "maksgrense for antal bokstavar som skal visast i vindauget",

		"m3u_add1": "songen blei lagd åt i m3u-spelelista",
		"m3u_addn": "{0} songer blei lagde åt i m3u-spelelista",
		"m3u_clip": "m3u-spelelista blei kopiert åt utklippstavla\n\nneste steg er å oppretta eit tekstdokument med filnamn som sluttar på <code>.m3u</code> og lime inn spelelista der",

		"gt_vau": "ikkje vis videofiler, berre spel lyden\">🎧",
		"gt_msel": "markér filer i staden for å åpne dei; ctrl-klikk filer for å overstyre$N$N&lt;em&gt;når aktiv: dobbelklikk ei fil / mappe for å åpne&lt;/em&gt;$N$NSnarvei: S\">markering",
		"gt_crop": "skjer ikona slik at dei passar betre\">✂",
		"gt_3x": "høgare oppløysing på ikon\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "trim",
		"gt_sort": "sortér",
		"gt_name": "namn",
		"gt_sz": "størr.",
		"gt_ts": "dato",
		"gt_ext": "type",
		"gt_c1": "redusér makslengde på filnamn",
		"gt_c2": "auk makslengde på filnamn",

		"sm_w8": "søker...",
		"sm_prev": "søkeresultata er frå eit tidlegare søk:\n  ",
		"sl_close": "lukk søkeresultat",
		"sl_hits": "visar {0} treff",
		"sl_moar": "hent fleire",

		"s_sz": "størr.",
		"s_dt": "dato",
		"s_rd": "sti",
		"s_fn": "namn",
		"s_ta": "meta",
		"s_ua": "up@",
		"s_ad": "avns.",
		"s_s1": "større enn ↓ MiB",
		"s_s2": "mindre enn ↓ MiB",
		"s_d1": "nyare enn &lt;dato&gt;",
		"s_d2": "eldre enn",
		"s_u1": "lasta opp etter",
		"s_u2": "og/eller før",
		"s_r1": "mappaamn inneheld",
		"s_f1": "filnamn inneheld",
		"s_t1": "song-info inneheld",
		"s_a1": "konkrete eigenskapar",

		"md_eshow": "visar forenkla ",
		"md_off": "[📜<em>readme</em>] er skrudd av i [⚙️] -- dokument skjult",

		"badreply": "Ugyldig svar frå serveren",

		"xhr403": "403: Høve nekta\n\nkanskje du blei logga ut? prøv å trykk F5",
		"xhr0": "ukjend (enten nettverksproblem eller serverkræsj)",
		"cf_ok": "om orsak -- liten tilfeldig kontroll, alt OK\n\nting skal fortsetja om ca. 30 sekund\n\nviss ikkje noko skjer, trykk F5 for å laste sida på nytt",
		"tl_xe1": "kunne ikkje hente undermapper:\n\nfeil ",
		"tl_xe2": "404: Mappa finnast ikkje",
		"fl_xe1": "kunne ikkje hente filer i mappa:\n\nfeil ",
		"fl_xe2": "404: Mappa finnast ikkje",
		"fd_xe1": "kan ikkje opprette ny mappe:\n\nfeil ",
		"fd_xe2": "404: Den overordna mappa finnast ikkje",
		"fsm_xe1": "kunne ikkje sende melding:\n\nfeil ",
		"fsm_xe2": "404: Den overordna mappa finnast ikkje",
		"fu_xe1": "kunne ikkje hente lista med nyleg opplastede filer frå serveren:\n\nfeil ",
		"fu_xe2": "404: Fila finnast ikkje??",

		"fz_tar": "ukomprimert gnu-tar arkiv, for linux og mac",
		"fz_pax": "ukomprimert pax-tar arkiv, litt treigare",
		"fz_targz": "gnu-tar pakket med gzip (nivå 3)$N$NNB: denne er veldig treig;$Nukomprimert tar er betre",
		"fz_tarxz": "gnu-tar pakket med xz (nivå 1)$N$NNB: denne er veldig treig;$Nukomprimert tar er betre",
		"fz_zip8": "zip med filnamn i utf8 (noko problematisk på windows 7 og eldre)",
		"fz_zipd": "zip med filnamn i cp437, for høggamle maskiner",
		"fz_zipc": "cp437 med tidlig crc32,$Nfor MS-DOS PKZIP v2.04g (oktober 1993)$N(øker behandlingstid på server)",

		"un_m1": "nedanfor kan du angre / slette filer som du nyleg har lastet opp, eller avbryte ufullstendige opplastinger",
		"un_upd": "oppdater",
		"un_m4": "eller viss du vil dele nedlastings-lenkene:",
		"un_ulist": "vis",
		"un_ucopy": "kopiér",
		"un_flt": "valgfritt filter:&nbsp; filnamn / filsti må inneholde",
		"un_fclr": "nullstill filter",
		"un_derr": 'unpost-sletting feilet:\n',
		"un_f5": 'noko gjekk galt, prøv å oppdatere lista eller trykk F5',
		"un_uf5": "om orsak, men du må laste sida på nytt (f.eks. ved å trykkje F5 eller CTRL-R) før denne opplastinga kan avbrytast",
		"un_nou": '<b>advarsel:</b> kan ikkje vise ufullstendige opplastingar akkurat no; klikk på oppdater-lenka om litt',
		"un_noc": '<b>advarsel:</b> angring av fullførte opplastingar er deaktivert i serverkonfigurasjonen',
		"un_max": "visar dei første 2000 filene (bruk filteret for å snevre inn)",
		"un_avail": "{0} nyleg opplasta filer kan slettast<br />{1} ufullstendige opplastingar kan avbrytast",
		"un_m2": "sortert etter opplastingstid; nyaste først:",
		"un_no1": "men nei, her var det jaggu ikkje noko som slettast kan",
		"un_no2": "men nei, her var det jaggu ingenting som passa overens med filteret",
		"un_next": "slett dei neste {0} filene nedanfor",
		"un_abrt": "avbryt",
		"un_del": "slett",
		"un_m3": "hentar lista med nyleg opplasta filer...",
		"un_busy": "slettar {0} filer...",
		"un_clip": "{0} lenkar kopiert åt utklippstavla",

		"u_https1": "du burde",
		"u_https2": "bytte åt https",
		"u_https3": "for høgare hastigheit",
		"u_ancient": 'nettlesaren din er prehistorisk -- mulig du burde <a href="#" onclick="goto(\'bup\')">bruke bup i staden for</a>',
		"u_nowork": "krev firefox 53+, chrome 57+, eller iOS 11+",
		"tail_2old": "krev firefox 105+, chrome 71+, eller iOS 14.5+",
		"u_nodrop": 'nettlesaren din er for gamal åt å laste opp filer ved å drage dei inn i vindauget',
		"u_notdir": "mottok ikkje mappa!\n\nnettlesaren din er for gamal,\nprøv å drage mappa inn i vindauget i staden for",
		"u_uri": "for å laste opp bilder frå andre nettlesarvindauge,\nslipp bildet rett på den store last-opp-knappen",
		"u_enpot": 'bytt åt <a href="#">enkelt UI</a> (gir sannsynleg raskere opplasting)',
		"u_depot": 'bytt åt <a href="#">snæsent UI</a> (gir sannsynleg treigare opplasting)',
		"u_gotpot": 'bytta åt eit enklare UI for å laste opp raskere,\n\ndu kan gjerne bytte tilbake altså!',
		"u_pott": "<p>filer: &nbsp; <b>{0}</b> ferdig, &nbsp; <b>{1}</b> feilet, &nbsp; <b>{2}</b> behandlast, &nbsp; <b>{3}</b> i kø</p>",
		"u_ever": "dette er den primitive opplastaren; up2k krev minst:<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'dette er den primitive opplastaren; <a href="#" id="u2yea">up2k</a> er betre',
		"u_uput": 'litt raskare (uten sha512)',
		"u_ewrite": 'du har ikkje høve til å skrive i denne mappa',
		"u_eread": 'du har ikkje høve til å lese i denne mappa',
		"u_enoi": 'filsøk er deaktivert i serverkonfigurasjonen',
		"u_enoow": "kan ikkje overskrive filer her (Delete-rettigheiten er nødvendig)",
		"u_badf": 'Disse {0} filene (av totalt {1}) kan ikkje leses, kanskje pga rettigheitsproblem i filsystemet på datamaskinen din:\n\n',
		"u_blankf": 'Disse {0} filene (av totalt {1}) er blanke / uten innhald; ønskjer du å laste dei opp uansett?\n\n',
		"u_applef": 'Disse {0} filene (av totalt {1}) er antakeleg uønska;\nTrykk <code>OK/Enter</code> for å HOPPE OVER disse filene,\nTrykk <code>Avbryt/ESC</code> for å LASTE OPP disse filene óg:\n\n',
		"u_just1": '\nFunkar kanskje betre viss du berre tar éi fil om gangen',
		"u_ff_many": 'Viss du bruker <b>Linux / MacOS / Android,</b> så kan dette antalet filer<br /><a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank"><em>kanskje</em> kræsje Firefox!</a> Viss det skjer, så prøv igjen (eller bruk Chrome).',
		"u_up_life": "Filene slettast frå serveren {0}\netter at opplastingen er fullført",
		"u_asku": 'Laste opp disse {0} filene åt <code>{1}</code>',
		"u_unpt": "Du kan angre / slette opplastinga med 🧯 oppe åt venstre",
		"u_bigtab": 'Vil no vise {0} filer...\n\nDette kan kræsje nettlesaren din. Fortsette?',
		"u_scan": 'Les mappane...',
		"u_dirstuck": 'Nettleseren din fekk ikkje høve åt å lese følgande {0} filer/mapper, så dei blir hoppa over:',
		"u_etadone": 'Ferdig ({0}, {1} filer)',
		"u_etaprep": '(forberedar opplasting)',
		"u_hashdone": 'synfaring ferdig',
		"u_hashing": 'les',
		"u_hs": 'serveren tenkjer...',
		"u_started": "filene blir no lasta opp 🚀",
		"u_dupdefer": "duplikat; vil bli håndtert åt slutt",
		"u_actx": "klikk her for å forhindre tap av<br />yting ved bytte åt andre vindauge/faner",
		"u_fixed": "OK!&nbsp; Løyste seg 👍",
		"u_cuerr": "kunne ikkje laste opp del {0} av {1};\nsikkert greit, fortsetjar\n\nfil: {2}",
		"u_cuerr2": "server nekta opplastinga (del {0} av {1});\nprøver igjen senere\n\nfil: {2}\n\nerror ",
		"u_ehstmp": "prøver igjen; se mld nederst",
		"u_ehsfin": "server nekta forespørselen om å ferdigstille filen; prøver igjen...",
		"u_ehssrch": "server nekta forespørselen om å utføre søk; prøver igjen...",
		"u_ehsinit": "server nekta forespørselen om å begynne ei ny opplasting; prøver igjen...",
		"u_eneths": "eit problem med nettverket gjorde at avtale om opplasting ikkje kunne inngås; prøver igjen...",
		"u_enethd": "eit problem med nettverket gjorde at filsjekk ikkje kunne utførast; prøver igjen...",
		"u_cbusy": "ventar på klarering frå server etter eit lite nettverksglipp...",
		"u_ehsdf": "serveren er full!\n\nprøver igjen regelmessig,\ni tilfelle nokon ryddar litt...",
		"u_emtleak1": "uff, det er mulig at nettlesaren din har ei minnelekkasje...\nForeslår",
		"u_emtleak2": ' helst at du <a href="{0}">byttar åt https</a>, eller ',
		"u_emtleak3": ' at du ',
		"u_emtleakc": 'prøver følgande:\n<ul><li>trykk F5 for å laste sida på nytt</li><li>så skru av &nbsp;<code>mt</code>&nbsp; brytaren under &nbsp;<code>⚙️ innstillinger</code></li><li>og prøv den same opplastinga igjen</li></ul>Opplasting vil gå litt treigare, men det får så vere.\nBeklager bryderiet!\n\nPS: feilen <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">skal vere fikset</a> i chrome v107',
		"u_emtleakf": 'prøver følgende:\n<ul><li>trykk F5 for å laste sida på nytt</li><li>så skru på <code>🥔</code> ("enkelt UI") i opplastaren</li><li>og prøv den same opplastingen igjen</li></ul>\nPS: Firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">fiksar forhåpentligvis feilen</a> ein eller annen gong',
		"u_s404": "ikkje funne på serveren",
		"u_expl": "forklar",
		"u_maxconn": "dei fleste nettlesarar tillet ikkje meir enn 6, men firefox lar deg øke grensen med <code>connections-per-server</code> i <code>about:config</code>",
		"u_tu": '<p class="warn">ADVARSEL: turbo er på, <span>&nbsp;avbrotne opplastingar vil muligens ikkje oppdagast og gjenopptakast; hald musepeikaren over turbo-knappen for meir info</span></p>',
		"u_ts": '<p class="warn">ADVARSEL: turbo er på, <span>&nbsp;søkeresultat kan vere feil; hold musepeikaren over turbo-knappen for meir info</span></p>',
		"u_turbo_c": "turbo er deaktivert i serverkonfigurasjonen",
		"u_turbo_g": 'turbo blei deaktivert fordi du ikkje har\nhøve åt å sjå mappeinnhold i dette volumet',
		"u_life_cfg": 'slett opplasting etter <input id="lifem" p="60" /> min (eller <input id="lifeh" p="3600" /> timar)',
		"u_life_est": 'opplastingen slettast <span id="lifew" tt="lokal tid">---</span>',
		"u_life_max": 'denne mappa tillet ikkje å \noppbevare filer i meir enn {0}',
		"u_unp_ok": 'opplasting kan angrast i {0}',
		"u_unp_ng": 'opplasting kan IKKE angrast',
		"ue_ro": 'du har ikkje høve åt skriving i denne mappa\n\n',
		"ue_nl": 'du er ikkje logga inn',
		"ue_la": 'du er logga inn som "{0}"',
		"ue_sr": 'du er i filsøk-modus\n\nbytt åt opplasting ved å klikke på forstørringsglaset 🔎 (ved siden av den store FILSØK-knappen) og prøv igjen\n\nsorry',
		"ue_ta": 'prøv å last opp igjen, det burde fungere no',
		"ue_ab": "den same filen er under opplasting åt ei anna mappe, og den må fullførast der før fila kan lastast opp andre plassar.\n\nDu kan avbryte og gløyme den påbegynte opplastinga ved hjelp av 🧯 oppe åt venstre",
		"ur_1uo": "OK: Fila blei lastet opp",
		"ur_auo": "OK: Alle {0} filene blei lastet opp",
		"ur_1so": "OK: Fila blei funne på serveren",
		"ur_aso": "OK: Alle {0} filene blei funne på serveren",
		"ur_1un": "Opplasting feila!",
		"ur_aun": "Alle {0} opplastingene gjekk feil!",
		"ur_1sn": "Fila finnast IKKE på serveren",
		"ur_asn": "Fann INGEN av dei {0} filene på serveren",
		"ur_um": "Ferdig;\n{0} opplastingar gjekk bra,\n{1} opplastingar gjekk feil",
		"ur_sm": "Ferdig;\n{0} filer blei funne,\n{1} filer finnast IKKJE på serveren",

		"lang_set": "passar det å laste sida på nytt?",
	},
	"pol": {
		"tt": "Polski",
		"cols": {
			"c": "przyciski akcji",
			"dur": "czas trwania",
			"q": "jakość / bitrate",
			"Ac": "kodek audio",
			"Vc": "kodek wideo",
			"Fmt": "format / kontener",
			"Ahash": "suma kontrolna audio",
			"Vhash": "suma kontrolna wideo",
			"Res": "rozdzielczość",
			"T": "rodzaj pliku",
			"aq": "jakość / bitrate audio",
			"vq": "jakość / bitrate wideo",
			"pixfmt": "podpróbkowanie / struktura pikseli",
			"resw": "rozdzielczość pozioma",
			"resh": "rozdzielczość pionowa",
			"chs": "kanały audio",
			"hz": "częstotliwość próbkowania"
		},

		"hks": [
			[
				"misc",
				["ESC", "zamknij różne rzeczy"],

				"file-manager",
				["G", "przełącz widok lista / siatka"],
				["T", "przełącz miniaturki / ikony"],
				["⇧ A/D", "wielkość miniaturki"],
				["ctrl-K", "usuń zaznaczone"],
				["ctrl-X", "wytnij zaznaczone do schowka"],
				["ctrl-C", "skopiuj zaznaczone do schowka"],
				["ctrl-V", "wklej (przenieś/skopiuj) tutaj"],
				["Y", "pobierz zaznaczone"],
				["F2", "zmień nazwę zaznaczonych"],

				"file-list-sel",
				["spacja", "przełącz zaznaczanie plików"],
				["↑/↓", "przenieś kursor zaznaczenia"],
				["ctrl ↑/↓", "przenieś kursor i widok"],
				["⇧ ↑/↓", "wybierz poprzedni/następny plik"],
				["ctrl-A", "wybierz wszystkie pliki/foldery"],
			], [
				"navigation",
				["B", "przełącz ścieżkę nawigacyjną / panel nawigacyjny"],
				["I/K", "poprzedni/następny folder"],
				["M", "folder nadrzędny (lub zwiń aktualny)"],
				["V", "przełącz foldery / pliki tekstowe w panelu nawigacyjnym"],
				["A/D", "rozmiar panelu nawigacyjnego"],
			], [
				"audio-player",
				["J/L", "poprzedni/następny utwór"],
				["U/O", "przejdź 10 sek. do tyłu/przodu"],
				["0..9", "przeskocz do 0%..90%"],
				["P", "odtwórz/pauza (również rozpoczyna)"],
				["S", "wybierz odtwarzany utwór"],
				["Y", "pobierz utwór"],
			], [
				"image-viewer",
				["J/L, ←/→", "poprzednie/następne zdjęcie"],
				["Home/End", "pierwsze/ostatnie zdjęcie"],
				["F", "pełny ekran"],
				["R", "obróć zgodnie ze wskaz. zegara"],
				["⇧ R", "obróć przeciwnie do ruchu wskaz. zegara"],
				["S", "wybierz zdjęcie"],
				["Y", "pobierz zdjęcie"],
			], [
				"video-player",
				["U/O", "przejdź 10 sek. do tyłu/przodu"],
				["P/K/Spacja", "odtwórz/pauza"],
				["C", "odtwarzaj następne po zakończeniu"],
				["V", "odtwarzaj w pętli"],
				["M", "wycisz"],
				["[ i ]", "ustaw opóźnienie pętli"],
			], [
				"textfile-viewer",
				["I/K", "poprzedni/następny plik"],
				["M", "zamknij plik"],
				["E", "edytuj plik"],
				["S", "wybierz plik (do wycięcia/skopiowania/zmiany nazwy)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Anuluj",

		"enable": "Włącz",
		"danger": "NIEBEZPIECZEŃSTWO",
		"clipped": "skopiowano do schowka",

		"ht_s1": "sekunda",
		"ht_s2": "sekundy",
		"ht_s5": "sekund",
		"ht_m1": "minuta",
		"ht_m2": "minuty",
		"ht_m5": "minut",
		"ht_h1": "godzina",
		"ht_h2": "godziny",
		"ht_h5": "godzin",
		"ht_d1": "dzień",
		"ht_d2": "dni",
		"ht_and": " i ",

		"goh": "panel sterowania",
		"gop": 'poprzedni plik/folder">poprzedni',
		"gou": 'nadrzędny folder">w górę',
		"gon": 'następny folder">następny',
		"logout": "Wyloguj ",
		"login": "Zaloguj się", //m
		"access": " dostęp",
		"ot_close": "zamknij pod-menu",
		"ot_search": "szukaj plików po atrybutach, ścieżce / nazwie, tagach muzyki, bądź dowolnej ich kombinacji$N$N&lt;code&gt;foo bar&lt;/code&gt; = musi zawierać «foo» oraz «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = musi zawierać «foo», lecz nie «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = musi zaczynać się od «yana» i być plikiem «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = zawierać dokładnie «try unite»$N$Nformatem daty jest iso-8601, czyli$N&lt;code&gt;2009-12-31&lt;/code&gt; lub &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: usuń ostatnio przesłane pliki lub przerwij przesyłanie",
		"ot_bup": "bup: podstawowe przesyłanie danych, wspiera nawet netscape 4.0",
		"ot_mkdir": "mkdir: tworzy nowy folder",
		"ot_md": "new-md: tworzy nowy dokument markdown",
		"ot_msg": "msg: wysyła wiadomość do loga serwera",
		"ot_mp": "opcje odtwarzacza multimediów",
		"ot_cfg": "opcje konfiguracji",
		"ot_u2i": 'up2k: przesyła pliki (jeżeli masz dostęp do zapisu) lub uruchomia tryb wyszukiwania, aby sprawdzić czy już istnieją na serwerze$N$Nprzesyłanie można wznowić, jest wielowątkowe i znaczniki czasu są zachowywane, lecz zużywa więcej procesora niż [🎈]&nbsp; (podstawowe przesyłanie)<br /><br />podczas przesyłania ta ikona zamienia się w wskaźnik postępu!',
		"ot_u2w": 'up2k: przesyła pliki z możliwością wznowienia (można zamknąć przeglądarkę i dokończyć przesyłanie plików później)$N$Njest wielowątkowy i zachowuje znaczniki czasu plików, lecz zużywa więcej procesora od [🎈]&nbsp; (podstawowego przesyłania)<br /><br />podczas przesyłania ta ikona zamienia się w wskaźnik postępu!',
		"ot_noie": 'Użyj przeglądarki Chrome / Firefox / Edge',

		"ab_mkdir": "stwórz folder",
		"ab_mkdoc": "stwórz dok. markdown",
		"ab_msg": "wyślij wiad. do logów serwera",

		"ay_path": "przejdź do folderów",
		"ay_files": "przejdź do plików",

		"wt_ren": "zmień nazwę zaznaczonych elementów$NSkrót: F2",
		"wt_del": "usuń zaznaczone elementy$NSkrót: ctrl-K",
		"wt_cut": "wytnij zaznaczone elementy &lt;small&gt;(aby wkleić gdzie indziej)&lt;/small&gt;$NSkrót: ctrl-X",
		"wt_cpy": "skopiuj zaznaczone pliki do schowka$N(aby wkleić gdzie indziej)$NSkrót: ctrl-C",
		"wt_pst": "wklej wcześniej wycięte/skopiowane zaznaczenie$NSkrót: ctrl-V",
		"wt_selall": "zaznacz wszystko$NHotkey: ctrl-A (when file focused)",
		"wt_selinv": "odwróć zaznaczenie",
		"wt_zip1": "pobierz folder jako archiwum",
		"wt_selzip": "pobierz zaznaczone jako archiwum",
		"wt_seldl": "pobierz zaznaczenie jako oddzielne pliki$NSkrót: Y",
		"wt_npirc": "skopiuj informacje o utworze w formacie irc",
		"wt_nptxt": "skopiuj informacje o utworze jako zwykły tekst",
		"wt_m3ua": "dodaj to playlisty m3u (kliknij <code>📻copy</code> kliknij)",
		"wt_m3uc": "skopiuj playlistę m3u do schowka",
		"wt_grid": "przełącz widok siatki / listy$NSkrót: G",
		"wt_prev": "poprzeni utwór$NSkrót: J",
		"wt_play": "odtwórz / pauza$NSkrót: P",
		"wt_next": "następny utwór$NSkrót: L",

		"ul_par": "przesyłane równolegle:",
		"ut_rand": "losuj nazwy plików",
		"ut_u2ts": "kopiuj znacznik ostatniej modyfikacji$Nz twojego systemu plików na serwer\">📅",
		"ut_ow": "nadpisywać istniejące pliki na serwerzę?$N🛡️: nigdy (wygeneruje nową nazwę)$N🕒: nadpisz jeśli pliki na serwerze są starsze niż przesyłane$N♻️: zawsze nadpisuj jeśli zawartość plików się różni",
		"ut_mt": "hashuj inne pliki podczas przesyłania$N$Nmożna wyłączyć w przypadku wystąpienia wąskiego gardła na CPU lub HDD",
		"ut_ask": 'pytaj o potwierdzenie rozpoczęcia przesyłania">💭',
		"ut_pot": "przyspiesz przesyłanie na słabszych urządzeniach,$Nupraszczając interfejs",
		"ut_srch": "nie przesyłaj plików, jedynie sprawdź czy istnieją$Njuż na serwerze (przeskanuje wszystkie foldery dostępne do odczytu)",
		"ut_par": "zatrzymuje przesyłanie jeśli wynosi 0$N$Nzwiększ w przypadku jeśli twoja sieć jest wolna / ma duże opóźnienia$N$Nustaw wartość 1 w sieci lokalnej lub w przypadku wolnego dysku serwerowego",
		"ul_btn": "upuść pliki / foldery<br>tutaj (lub kliknij mnie)",
		"ul_btnu": "P R Z E Ś L I J",
		"ul_btns": "S Z U K A J",

		"ul_hash": "hashowanie",
		"ul_send": "przesyłanie",
		"ul_done": "gotowe",
		"ul_idle1": "nic się jeszcze nie przesyła",
		"ut_etah": "średnia prędkość &lt;em&gt;hashowania&lt;/em&gt i przewidywany czas do końca",
		"ut_etau": "średnia prędkość &lt;em&gt;przesyłania&lt;/em&gt i przewidywany czas do końca",
		"ut_etat": "średnia prędkość &lt;em&gt;ogólna&lt;/em&gt i przewidywany czas do końca",

		"uct_ok": "zakończone pomyślnie",
		"uct_ng": "zakończono niepowodzeniem (odrzucono, nie znaleziono, itp.)",
		"uct_done": "zakończono z błędami",
		"uct_bz": "w trakcie (oblicznie sumy kontrolnej, przesyłanie)",
		"uct_q": "oczekujące",

		"utl_name": "nazwa pliku",
		"utl_ulist": "lista",
		"utl_ucopy": "kopia",
		"utl_links": "linki",
		"utl_stat": "status",
		"utl_prog": "postęp",

		// keep short:
		"utl_404": "404",
		"utl_err": "BŁĄD",
		"utl_oserr": "błąd OS",
		"utl_found": "znaleziono",
		"utl_defer": "opóźnij",
		"utl_yolo": "YOLO",
		"utl_done": "gotowe",

		"ul_flagblk": "pliki zostały zakolejkowane,</b><br>lecz przesyłanie up2k już trwa (w innej zakładce),<br>oczekuję na zakończenie",
		"ul_btnlk": "przełącznik zablokowany przez konfigurację serwera",

		"udt_up": "Prześlij",
		"udt_srch": "Szukaj",
		"udt_drop": "upuść tutaj",

		"u_nav_m": '<h6>co my tu mamy?</h6><code>Enter</code> = Pliki (jeden lub wiecej)\n<code>ESC</code> = Jeden folder (włącznie z podfolderami)',
		"u_nav_b": '<a href="#" id="modal-ok">Pliki</a><a href="#" id="modal-ng">Jeden folder</a>',

		"cl_opts": "przełączniki",
		"cl_themes": "motyw",
		"cl_langs": "język",
		"cl_ziptype": "pobieranie folderów",
		"cl_uopts": "przełączniki przesyłania (up2k)",
		"cl_favico": "favicon (ikona w przeglądarce)",
		"cl_bigdir": "duże foldery",
		"cl_hsort": "#sortowanie",
		"cl_keytype": "notacja klucza",  // not sure
		"cl_hiddenc": "ukryte kolumny",
		"cl_hidec": "ukryj",
		"cl_reset": "zresetuj",
		"cl_hpick": "kliknij nagłówki kolumn, aby ukryć je w tabeli niżej",
		"cl_hcancel": "ukrywanie kolumn przerwane",

		"ct_grid": '田 siatka',
		"ct_ttips": '◔ ◡ ◔">ℹ️ podpowiedzi',
		"ct_thumb": 'w widoku siatki, przełącz ikony i miniaturki$NSkrót: T">🖼️ miniaturki',
		"ct_csel": 'użyj CTRL i SHIFT do wybierania plików w widoku siatki">wybierz',
		"ct_ihop": 'przejdź do ostatniego pliku po zamknięciu przeglądarki obrazów">g⮯',
		"ct_dots": 'pokaż ukryte pliki (jeśli pozwala serwer)">ukryte',
		"ct_qdel": 'pytaj o potwierdzenie przy usuwaniu tylko raz">pyt. us.',
		"ct_dir1st": 'pokazuj foldery na początku">📁 najpierw',
		"ct_nsort": 'naturalne sortowanie (dla numerowanych plików)">nsort',
		"ct_utc": 'pokaż wszystkie daty/czas w UTC">UTC',
		"ct_readme": 'pokazuj README.md w folderach">📜 readme',
		"ct_idxh": 'pokazuj plik index.html zamiast zawartości folderu">htm',
		"ct_sbars": 'pokazuj paski przewijania">⟊',

		"cut_umod": "uaktualnij znacznik ostatniej modyfikacji pliku, tak aby pasował do pliku lokalnego jeżeli plik już istnieje na serwerze (wymaga dostępu zapisu i usuwania)\">📅 ponownie",

		"cut_turbo": "przycisk „raz się żyje”, raczej NIE POWINIENEŚ tego włączać:$N$Nużywaj jeśli przesyłano ogromną liczbę plików i z jakiegoś powodu musisz przesłać pliki ponownie, kontynuując jak najszybciej$N$Nzamienia sprawdzanie sumy kontrolnej plików prostym <em>&quot;czy ten plik jest tego samego rozmiaru jak ten na serwerze?&quot;</em> więc jeśli pliki różnią się zawartością, ale są tego samego rozmiaru, NIE ZOSTANĄ przesłane ponownie$N$Nta opcja powinna zostać wyłączona po zakończeniu przesyłania, i potem &quot;przesłać&quot; te same pliki ponownie w celu weryfikacji\">turbo",

		"cut_datechk": "przy wyłączonym przycisku turbo nic nie robi$N$Nleciutko zmniejsza czynnik „raz się żyje”; dodatkowo sprawdza czy znaczniki modyfikacji pliku przesyłanego zgadzają się z serwerem$N$N<em>teorytycznie</em> powinno złapać to większość niedokończonych / uszkodzonych plików, lecz nie jest zamiennikiem wykonania ponownego sprawdzenia bez włączonego trybu turbo\">spr-daty",

		"cut_u2sz": "rozmiar (w MiB) każdego kawałka do przesłania; większe wartości szybciej latają po Atlantyku. Mniejsze wartości działają lepiej na bardzo niestabilnych połączeniach (neostrada?)",

		"cut_flag": "zapewnia, że tylko jedna karta przesyła dane w danym momencie$N -- opcja musi być włączona na innych kartach $N - dotyczy tylko kart w tej samej domenie",

		"cut_az": "przesyła pliki w kolejności alfabetycznej, zamiast rozpocząć od najmniejszego pliku$N$Nkolejność alfabetyczna może ułatwić oszacowanie, co mogło pójść nie tak na serwerze, lecz lekko spowalnia przesyłanie po światłowodzie lub w sieci lokalnej",

		"cut_nag": "powiadomienie systemowe po zakończeniu przesyłania$N(tylko jeśli przeglądarka lub karta nie jest aktywna)",
		"cut_sfx": "sygnał dźwiękowy po zakończeniu przesyłania$N(tylko jeśli przeklądarka lub karta nie jest aktywna)",

		"cut_mt": "używaj wielowątkowości, aby przyspieszyć obliczanie sumy kontrolnej plików$N$Nużywa web workerów i wymaga$Nwięcej pamięci RAM (do 512 MiB)$N$Nprzyspiesza https o 30% i http 4,5-krotnie\">ww",

		"cut_wasm": "używaj WASM zamiast wbudowanego hashera przeglądarki; zwiększa prędkość na Chrome'o-pochodnych przeglądarkach, zwiększając zużycie procesora, ponadto wiele starszych wersji Chrome'a zawiera błędy powodujące zeżarcie całej pamięci RAM komputera i przymusowe zamknięcie przeglądarki jeżeli ta opcja jest włączona\">wasm",

		"cft_text": "tekst favicon (aby wyłączyć, usuń zawartość i przeładuj stronę)",
		"cft_fg": "kolor tekstu",
		"cft_bg": "kolor tła",

		"cdt_lim": "maksymalna liczba plików do pokazania na raz w folderze",
		"cdt_ask": "przy przewijaniu w dół,$Nzapytaj co robić,$Nzamiast wczytywać kolejne pliki",
		"cdt_hsort": "ile zasad sortowania (&lt;code&gt;,sorthref&lt;/code&gt;) zawierać w generowanych linkach multimediów. Wartość 0 sprawi, że zasady sortowania zawarte w linkach multimediów przy otwarciu również będą ignorowane",

		"tt_entree": "pokaż panel nawigacyjny (panel boczny z drzewem folderów)$NSkrót: B",
		"tt_detree": "pokaż ślad nawigacyjny$NSkrót: B",
		"tt_visdir": "przewiń do wybranego folderu",
		"tt_ftree": "przełącz drzewo folderów / pliki tekstowe$NSkrót: V",
		"tt_pdock": "pokaż foldery nadrzędne w przypiętym u góry panelu",
		"tt_dynt": "rozszerzaj panel wraz z drzewem",
		"tt_wrap": "zawijaj tekst",
		"tt_hover": "pokazuj za długie linie po najechaniu kursorem$N( psuje przewijanie gdy $N&nbsp; kursor nie jest w lewym marginesie )",

		"ml_pmode": "na końcu folderu...",
		"ml_btns": "komendy",
		"ml_tcode": "transkoduj",
		"ml_tcode2": "transkoduj do",
		"ml_tint": "odcień",
		"ml_eq": "korektor dźwięku (equalizer)",
		"ml_drc": "kompresor zasięgu dynamiki",

		"mt_loop": "pętla/powtarzaj jeden utwór\">🔁",
		"mt_one": "zatrzymaj po jednym utworze\">1️⃣",
		"mt_shuf": "odtwarzaj losowo w każdym folderze\">🔀",
		"mt_aplay": "autoodtwarzanie po kliknięciu linku do tego serwera, zawierającego identyfikator utworu$N$Nwyłączenie tej opcji zapobiegnie aktualizowaniu adresu strony podczas odtwarzania muzyki, aby zapobiec autoodtwarzaniu przy utracie ustawień\">a▶",
		"mt_preload": "rozpocznij ładowanie kolejnego utworu blisko końca aktualnego w celu uzyskania odtwarzania bez przerw\">preload",
		"mt_prescan": "przechodzi do następnego folderu przed zakończeniem ostatniego utworu,$Naby udobruchać przeglądarkę,$Nżeby nie zatrzymała odtwarzania\">naw",
		"mt_fullpre": "próbuj zbuforować cały utwór;$N✅ włącz na <b>niestabilnych</b> połączeniach,$N❌ <b>wyłącz</b> na wolnych połączeniach\">pełnebuf",
		"mt_fau": "nie zatrzymuj muzyki jeśli następna piosenka będzie się zbyt wolno buforować na telefonach (może sprawić, że tagi będą się niepoprawnie wyświetlać)\">☕️",
		"mt_waves": "falisty pasek:$Npokazuj amplitudę dźwięku w pasku utworu\">~s",
		"mt_npclip": "pokaż przyciski kopiowania aktualnie odtwarzanego utworu\">/np",
		"mt_m3u_c": "pokaż przyciski kopiowania$Nwybranych piosenek jako playlista m3u8\">📻",
		"mt_octl": "integracja z systemem operacyjnym (przyciski multimedialne / informacje o utworze)\">os-int",
		"mt_oseek": "zezwól na przewijanie utworu poprzez integrację z systemem$N$Nuwaga: na niektórych urządzeniach (iPhone'y),$Nzamienia przycisk następnej piosenki\">seek",
		"mt_oscv": "pokaż okładkę albumu w widoku systemu\">okładka",
		"mt_follow": "podążaj za odtwarzanym utworem przewijając widok\">🎯",
		"mt_compact": "kompaktowe sterowanie\">⟎",
		"mt_uncache": "wyczyść pamięć podręczną &nbsp;(spróbuj jeśli przeglądarka$Nzachowała zepsutą kopię utworu, przez co nie odtwarza się ona)\">uncache",
		"mt_mloop": "odtwarzaj utwory w folderze w pętli\">🔁 loop",
		"mt_mnext": "wczytaj następny folder i kontynuuj\">📂 next",
		"mt_mstop": "zatrzymaj odtwarzanie\">⏸ stop",
		"mt_cflac": "przekonwertuj format flac / wav na {0}\">flac",
		"mt_caac": "przekonwertuj format aac / m4a na {0}\">aac",
		"mt_coth": "przekonwertuj wszystkie inne formaty (nie będące mp3) na {0}\">oth",
		"mt_c2opus": "najlepszy wybór dla komputerów, laptopów i urządzeń z androidem\">opus",
		"mt_c2owa": "opus-weba, dla iOS 17.5 i nowszych\">owa",
		"mt_c2caf": "opus-caf, dla iOS 11 do 17\">caf",
		"mt_c2mp3": "używaj na bardzo starych urządzeniach\">mp3",
		"mt_c2flac": "najlepsza jakość dźwięku, ale ogromne pliki do pobrania\">flac", //m
		"mt_c2wav": "nieskompresowane odtwarzanie (jeszcze większe)\">wav", //m
		"mt_c2ok": "cudownie, dobry wybór",
		"mt_c2nd": "ten format nie jest rekomendowany dla twojego urządzenia, ale nadal jest w porządku",
		"mt_c2ng": "wygląda na to, że to urządzenie nie wspiera tego formatu, lecz spróbujmy i tak",
		"mt_xowa": "iOS zawiera błędy uniemożliwiające odtwarzanie w tle używając tego formatu; wybierz caf lub mp3",
		"mt_tint": "jasność tła (0-100) paska,$Naby zmniejszyć widoczność buforowania",
		"mt_eq": "włącza korektor dźwięku (equalizer) i kontrolę wzmocnienia dźwięku;$N$Nboost &lt;code&gt;0&lt;/code&gt; = standardowa głośność 100% (niezmodyfikowana)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = standardowe stereo (niezmodyfikowane)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% crossfeed lewo-prawo$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = usuwanie wokalu :^)$N$Nwłączenie korektora sprawia, że albumy bezprzerwowe są w pełni bez przerw, więc jeśli jest to dla ciebie ważne, zostaw wszystko na 0 (poza width = 1)",
		"mt_drc": "włącza kompresor zakresu dynamiki (normalizacja głośności); włącza również korektor w celu zbalansowania tego spaghetti, więc ustaw wszystkie opcje korektora, oprócz 'width',na 0, jeśli go nie chcesz$N$Nobniża głośność audio nad THRESHOLD (próg) dB; dla każdego RATIO (współczynnika) dB, będącego ponad THRESHOLDem jest 1 dB wyjścia, więc domyślne wartości progu -24 i współczynnika 12 znaczą, że nigdy nie powinno być głośniej niż -22 dB i bezpieczne jest zwiększenie wzmocnienia korektora do 0.8, lub nawet 1.8 z ATK 0 i ogromnym RLS, jak 90 (działa tylko na firefoxie, inne przeglądarki mają limit RLS 1)$N$N(na wikipedii tłumaczą to dużo lepiej)",

		"mb_play": "odtwórz",
		"mm_hashplay": "odtworzyć ten plik audio?",
		"mm_m3u": "naciśnij <code>Enter/OK</code>, aby odtworzyć\nnaciśnij <code>ESC/Anuluj</code>, aby edytować",
		"mp_breq": "wymagany jest Firefox 82+, Chrome 73+ lub iOS 15+",
		"mm_bload": "wczytywanie...",
		"mm_bconv": "konwertowanie do {0}, proszę czekać...",
		"mm_opusen": "ta przeglądarka nie może odtwarzać plików aac / m4a;\ntranskodowanie do formatu opus włączone",
		"mm_playerr": "odtwarzanie nie powiodło się: ",
		"mm_eabrt": "Odtwarzanie zostało przerwane",
		"mm_enet": "Połączenie z internetem jest słabe",
		"mm_edec": "Ten plik wydaje się uszkodzony??",
		"mm_esupp": "Twoja przeglądarka nie rozumie tego formatu audio",
		"mm_eunk": "Nieznany błąd",
		"mm_e404": "Nie można odtworzyć; błąd 404: Nie znaleziono pliku.",
		"mm_e403": "Nie można odtworzyć; błąd 403: Odmowa dostępu.\n\nSpróbuj przeładować stronę (F5), może cię wylogowało",
		"mm_e500": "Nie można odtworzyć; błąd 500: Sprawdź logi serwera.",
		"mm_e5xx": "Nie można odtworzyć; błąd serwera",
		"mm_nof": "nie znaleziono więcej plików audio",
		"mm_prescan": "Szukanie kolejnego utworu...",
		"mm_scank": "Znaleziono następną piosenkę:",
		"mm_uncache": "wyczyszczono pamięć podręczną; wszystkie utwory zostaną pobrane ponownie przy następnym odtworzeniu",
		"mm_hnf": "ten utwór już nie istnieje",

		"im_hnf": "ten obraz już nie istnieje",

		"f_empty": 'ten folder jest pusty',
		"f_chide": 'schowa kolumnę «{0}»\n\nkolumny można ponownie pokazać w zakładce ustwaień',
		"f_bigtxt": "ten plik waży {0} MiB -- na pewno pokazać jako tekst?",
		"f_bigtxt2": "odczytać jedynie koniec pliku? włączy również śledzenie, pokazując nowo-dodane linie tekstu w czasie rzeczywistym",
		"fbd_more": '<div id="blazy">pokazuję <code>{0}</code> z <code>{1}</code> plików; <a href="#" id="bd_more">pokaż {2}</a> lub <a href="#" id="bd_all">pokaż wszystko</a></div>',
		"fbd_all": '<div id="blazy">pokazuję <code>{0}</code> z <code>{1}</code> files; <a href="#" id="bd_all">pokaż wszystko</a></div>',
		"f_anota": "{0} z {1} elementów zostało wybranych;\naby pokazać cały folder, zjedź na dół",

		"f_dls": 'linki do plików w aktualnym folderze\nzostały zmienione w linki pobierania',

		"f_partial": "Aby bezpiecznie pobrać plik, który aktualnie jest przesyłany, wybierz plik o tej samej nazwie, lecz bez rozszerzenia <code>.PARTIAL</code>. Żeby to zrobić, naciśnij ANULUJ lub klawisz ESC.\n\nWciśnięcie OK / Enter zignoruje to ostrzeżenie i pobierze plik tymczasowy <code>.PARTIAL</code>, który prawie z pewnością będzie zepsuty",

		"ft_paste": "wklej {0} elementów$NSkrót: ctrl-V",
		"fr_eperm": 'nie można zmienić nazwy:\nnie posiadasz uprawnienia „move” w tym folderze',
		"fd_eperm": 'nie można usunąć:\nnie posiadasz uprawnienia „delete” w tym folderze',
		"fc_eperm": 'nie można wyciąć:\nnie posiadasz uprawnienia „move” w tym folderze',
		"fp_eperm": 'nie można wkleić:\nnie posiadasz uprawnienia „write” w tym folderze',
		"fr_emore": "wybierz przynajmniej jeden element do zmiany nazwy",
		"fd_emore": "wybierz przynajmniej jeden element do usunięcia",
		"fc_emore": "wybierz przynajmniej jeden element do wycięcia",
		"fcp_emore": "wybierz przynajmniej jeden element do skopiowania",

		"fs_sc": "udostępnij ten folder",
		"fs_ss": "udostępnij zaznaczone pliki",
		"fs_just1d": "nie można wybrać więcej niż jednego folderu,\nani mieszać plików i folderów w jednym zaznaczeniu",
		"fs_abrt": "❌ przerwij",
		"fs_rand": "🎲 losuj nazwę",
		"fs_go": "✅ stwórz udostępnienie",
		"fs_name": "nazwa",
		"fs_src": "źródło",
		"fs_pwd": "hasło",
		"fs_exp": "wygaśnięcie",
		"fs_tmin": "min",
		"fs_thrs": "godz.",
		"fs_tdays": "dni",
		"fs_never": "na zawsze",
		"fs_pname": "opcjonalna nazwa linku; zostanie wylosowana jeśli pusta",
		"fs_tsrc": "plik lub folder do udostępnienia",
		"fs_ppwd": "hasło (opcjonalnie)",
		"fs_w8": "udostępnianie...",
		"fs_ok": "naciśnij <code>Enter/OK</code>, aby skopiować do schowka\nnaciśnij <code>ESC/Anuluj</code>, aby zamknąć",

		"frt_dec": "może naprawić niektóre zepsute nazwy plików\">dekoduj-url",
		"frt_rst": "zresetuj zmodyfikowane nazwy plików do oryginalnych\">↺ zresetuj",
		"frt_abrt": "przerwij i zamknij to okno\">❌ anuluj",
		"frb_apply": "ZASTOSUJ ZMIANĘ NAZWY",
		"fr_adv": "zmiana nazwy hurtowa / metadanych / wzorcem\">zaawansowane",
		"fr_case": "rozróżnianie wielkości liter w regex\">wlit",
		"fr_win": "nazwy bezpieczne dla systemu Windows; zamienia symbole <code>&lt;&gt;:&quot;\\|?*</code> na japońskie odpowiedniki\">win",
		"fr_slash": "zamienia <code>/</code> symbolem, który nie tworzy nowych folderów\">brak /",
		"fr_re": "wzorzec wyszukiwania regex stosowany do oryginalnych nazw plików; do grup przechwytywania można się odwołać w polu formatu poniżej, np.  &lt;code&gt;(1)&lt;/code&gt; i &lt;code&gt;(2)&lt;/code&gt; itd.",
		"fr_fmt": "inspirowane programem foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; zostaje zamienione na tytuł utworu,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; pomija [tą] część jeśli pole artysty jest puste$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; wyrównuje numer utworu do 2 cyfr (np. 01, 06, 09, 16)",
		"fr_pdel": "usuń",
		"fr_pnew": "zapisz jako",
		"fr_pname": "podaj nazwę nowego szablonu",
		"fr_aborted": "anulowano",
		"fr_lold": "poprzednia nazwa",
		"fr_lnew": "nowa nazwa",
		"fr_tags": "znaczniki dla wybranych plików (tylko do odczytu, w celach informacyjnych):",
		"fr_busy": "zmienianie nazwy {0} plików...\n\n{1}",
		"fr_efail": "zmiana nazwy zakończona niepowodzeniem:\n",
		"fr_nchg": "{0} nowych nazw zostało zmienionych przez opcje <code>win</code> i/lub <code>brak /</code>\n\nKontynuować ze zmienionymi nazwami?",

		"fd_ok": "usunięto",
		"fd_err": "usuwanie zakończone niepowodzeniem:\n",
		"fd_none": "nie usunięto nic; usunięcie mogło zostać zablokowane przez konfigurację serwera (xbd)?",
		"fd_busy": "usuwanie {0} elementów...\n\n{1}",
		"fd_warn1": "USUNĄĆ {0} elementów?",
		"fd_warn2": "<b>OSTATNIA SZANSA!</b> Tej operacji nie da się cofnąć. Usunąć?",

		"fc_ok": "wycięto {0} elementów",
		"fc_warn": 'wycięto {0} elementów,\n\nlecz można je wkleić tylko w <b>tej</b> karcie\n(ze względu na ogromną ilość wybranych elementów)',

		"fcc_ok": "skopiowano {0} elementów do schowka",
		"fcc_warn": 'skopiowano {0} elementów,\n\nlecz można je wkleić tylko w <b>tej</b> karcie\n(ze względu na ogromną ilość wybranych elementów)',

		"fp_apply": "zastosuj te nazwy",
		"fp_ecut": "najpierw wytnij lub skopiuj pliki / foldery, aby je wkleić / przenieść\n\nuwaga: można wycinać / wklejać pomiędzy różnymi kartami przeglądarki",
		"fp_ename": "Nie udało się przenieść {0} elementów, gdyż ich nazwy już istnieją w tym folderze. Nadaj im nowe nazwy poniżej, bądź zostaw pole nazwy puste, aby je pominąć:",
		"fcp_ename": "Nie udało się przekopiować {0} elementów, gdyż ich nazwy już istnieją w tym folderze. Nadaj im nowe nazwy poniżej, bądź zostaw pole nazwy puste, aby je pominąć:",
		"fp_emore": "pozostało jeszcze kilka kolizji nazw plików do poprawy",
		"fp_ok": "przeniesiono",
		"fcp_ok": "przekopiowano",
		"fp_busy": "przenoszenie {0} elementów...\n\n{1}",
		"fcp_busy": "kopiowanie {0} elementów...\n\n{1}",
		"fp_abrt": "przerywanie...", //m
		"fp_err": "nie udało się przenieść:\n",
		"fcp_err": "nie udało się skopiować:\n",
		"fp_confirm": "przenieść tutaj {0} elementy(ów)?",
		"fcp_confirm": "skopiować tutaj {0} elementy(ów)?",
		"fp_etab": 'nie udało się odczytać schowka z innej karty przeglądarki',
		"fp_name": "przesyłanie pliku z twojego urządzenia. Nadaj nazwę:",
		"fp_both_m": '<h6>wybierz metodę wklejenia</h6><code>Enter</code> = Przenieś {0} pliki(ów) z «{1}»\n<code>ESC</code> = Prześlij {2} pliki(ów) z twojego urządzenia',
		"fcp_both_m": '<h6>wybierz metodę wklejenia</h6><code>Enter</code> = Skopiuj {0} pliki(ów) z «{1}»\n<code>ESC</code> = Prześlij {2} pliki(ów) z twojego urządzenia',
		"fp_both_b": '<a href="#" id="modal-ok">Przenieś</a><a href="#" id="modal-ng">Prześlij</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopiuj</a><a href="#" id="modal-ng">Prześlij</a>',

		"mk_noname": "wpisz nazwę do pola po lewej zanim to zrobisz :p",

		"tv_load": "Wczytywanie pliku tekstowego:\n\n{0}\n\n{1}% (wczytano {2} z {3} MiB)",
		"tv_xe1": "nie udało się wczytać pliku:\n\nbłąd ",
		"tv_xe2": "404, nie znaleziono pliku",
		"tv_lst": "lista plików tekstowych w",
		"tvt_close": "powróć do widoku folderów$NSkrót: M (lub Esc)\">❌ zamknij",
		"tvt_dl": "pobierz ten plik$NHotkey: Y\">💾 pobierz",
		"tvt_prev": "pokaż poprzedni dokument$NSkrót: i\">⬆ poprzedni",
		"tvt_next": "pokaż następny dokument$NSkrót: K\">⬇ następny",
		"tvt_sel": "wybierz plik &nbsp; ( do wycięcia / skopiowania / usunięcia / itp. )$NSkrót: S\">wyb",
		"tvt_edit": "otwórz plik w edytorze tekstu$NSkrót: E\">✏️ edytuj",
		"tvt_tail": "śledź zmiany w pliku; pokazuj nowe linie w czasie rzeczywistym\">📡 śledź",
		"tvt_wrap": "zawijaj tekst\">↵",
		"tvt_atail": "utrzymuj widok na dole strony\">⚓",
		"tvt_ctail": "dekoduj kolory terminala (sekwencje sterujące ANSI)\">🌈",
		"tvt_ntail": "limit przewijania (ile bajtów tekstu przechowywać w pamięci)",

		"m3u_add1": "dodano utwór do playlisty m3u",
		"m3u_addn": "dodano {0} utwory(ów) do playlisty m3u",
		"m3u_clip": "skopiowano playlistę m3u do schowka\n\nutwórz",

		"gt_vau": "nie pokazuj obrazu, odtwarzaj tylko dźwięk\">🎧",
		"gt_msel": "wybierz pliki; kliknij plik z wciśniętym klawiszem CTRL, aby zastąpić$N$N&lt;em&gt;gdy tryb jest aktywny, kliknij dwukrotnie na plik / folder, żeby go otworzyć&lt;/em&gt;$N$NSkrót: S\">wybierz wiele",
		"gt_crop": "kadruj miniaturki do środka\">kadruj",
		"gt_3x": "miniaturki w wysokiej rozdzielczości\">3x",
		"gt_zoom": "przybliż",
		"gt_chop": "przytnij",
		"gt_sort": "sortuj według",
		"gt_name": "nazwa",
		"gt_sz": "rozmiar",
		"gt_ts": "data",
		"gt_ext": "typ",
		"gt_c1": "przycinaj większą część nazw plików (pokazuj mniej)",
		"gt_c2": "przycinaj mniejszą część nazw plików (pokazuj więcej)",

		"sm_w8": "wyszukiwanie...",
		"sm_prev": "wyniki wyszukiwania poniżej pochodzą z poprzedniego zapytania:\n  ",
		"sl_close": "zamknij wyniki wyszukiwania",
		"sl_hits": "pokazuję {0} wyniki(ów)",
		"sl_moar": "pokaż więcej",

		"s_sz": "rozmiar",
		"s_dt": "data",
		"s_rd": "ścieżka",
		"s_fn": "nazwa",
		"s_ta": "znaczniki",
		"s_ua": "data przesłania",
		"s_ad": "zaawansowane",
		"s_s1": "min. rozmiar (MiB)",
		"s_s2": "maks. rozmiar (MiB)",
		"s_d1": "min. data iso8601",
		"s_d2": "maks. data iso8601",
		"s_u1": "przesłane po",
		"s_u2": "i/lub przed",
		"s_r1": "ścieżka zawiera &nbsp; (oddzielone spacją)",
		"s_f1": "nazwa zawiera &nbsp; (odwróć za pomocą -nope)",
		"s_t1": "znaczniki zawierają &nbsp; (^=start, koniec=$)",
		"s_a1": "dokładne właściwości metadanych",

		"md_eshow": "nie można wyświetlić ",
		"md_off": "[📜<em>readme</em>] wyłączone w [⚙️] -- dokument ukryty",

		"badreply": "Nie udało się przeanalizować odpowiedzi serwera",

		"xhr403": "403: Odmowa dostępu.\n\nSpróbuj przeładować stronę (F5), możliwe, że cię wylogowano",
		"xhr0": "nieznany (być może utracono połączenie z serwerem, lub jest on nieaktywny)",
		"cf_ok": "przepraszamy, włączyła się ochrona przed DD" + wah + "oS\n\nwszystko powinno wrócić do normy za około 30 sekund\n\njeśli nic się nie zmieni, naciśnij klawisz F5, aby przeładować stronę",
		"tl_xe1": "nie można wyświetlić podfolderów:\n\nbłąd ",
		"tl_xe2": "404: Nie znaleziono folderu",
		"fl_xe1": "nie można wyświetlić plików w folderze:\n\nbłąd ",
		"fl_xe2": "404: Nie znaleziono folderu",
		"fd_xe1": "nie można stworzyć podfolderu:\n\nbłąd ",
		"fd_xe2": "404: Nie znaleziono folderu nadrzędnego",
		"fsm_xe1": "nie można wysłać wiadomości:\n\nbłąd ",
		"fsm_xe2": "404: Nie znaleziono folderu nadrzędnego",
		"fu_xe1": "nie udało się wczytać listy unpost z serwera:\n\nbłąd ",
		"fu_xe2": "404: Nie znaleziono pliku??",

		"fz_tar": "nieskompresowane archiwum gnu-tar (linux / mac)",
		"fz_pax": "nieskompresowane archiwum tar w formacie pax (wolniejsze)",
		"fz_targz": "gnu-tar z kompresją gzip poziomu 3.,$N$Nzazwyczaj bardzo wolne, używaj nieskompresowanego tar",
		"fz_tarxz": "gnu-tar z kompresją xz poziomu 3.$N$Nzazwyczaj bardzo wolne, używaj nieksompresowanego tar",
		"fz_zip8": "zip z nazwami plików UTF-8 (może działać nieprawidłowo na systemie Windows 7 i starszych)",
		"fz_zipd": "zip z nazwami plików cp437, dobre dla bardzo starego oprogramowania",
		"fz_zipc": "cp437 z CRC32 obliczonym wcześniej,$Ndla MS-DOS PKZIP v2.04g (październik 1993)$N(przetwarzanie do pobrania trwa dłużej)",

		"un_m1": "można usunąć ostatnio przesłane pliki (lub przerwać trwające) poniżej",
		"un_upd": "odśwież",
		"un_m4": "lub udostępnij pliki widoczne poniżej:",
		"un_ulist": "pokaż",
		"un_ucopy": "kopiuj",
		"un_flt": "filtruj (opcjonalnie):&nbsp; URL musi zawierać",
		"un_fclr": "wyczyść kryteria filtrowania",
		"un_derr": 'nie udało się usunąć unpost:\n',
		"un_f5": 'coś poszło nie tak, spróbuj odświeżyć lub wciśnij F5',
		"un_uf5": "przed przerwaniem przesyłania trzeba odświeżyć stronę (za pomocą CTRL-R lub F5)",
		"un_nou": '<b>ostrzeżenie:</b> serwer jest aktualnie zbyt obciążony, żeby pokazać niedokończone przesłania; kliknij link "odśwież" za chwilę',
		"un_noc": '<b>ostrzeżenie:</b> unpost w pełni przesłanych plików jest wyłączone/zabronione w konfiguracji serwera',
		"un_max": "pokazuję pierwsze 2000 plików (użyj filtrowania)",
		"un_avail": "{0} ostatnio przesłanych elementów może zostać usunięte<br />{1} niedokończonych można przerwać",
		"un_m2": "przesortowano po czasie przesłania; najnowsze elementy pierwsze: ",
		"un_no1": "cholibka! żaden przesłany element nie jest wystarczająco niedawny",
		"un_no2": "cholibka! żaden przesłany element pasujący do filtra nie jest wystarczająco niedawny",
		"un_next": "usuń następne {0} pliki(ów) poniżej",
		"un_abrt": "przerwij",
		"un_del": "usuń",
		"un_m3": "wczytywanie ostatnio przesłanych elementów...",
		"un_busy": "usuwanie {0} plików...",
		"un_clip": "skopiowano {0} linków do schowka",

		"u_https1": "powinieneś przejść",
		"u_https2": "na HTTPS w celu",
		"u_https3": "uzyskania lepszej wydajności",
		"u_ancient": 'twoja przeglądarka jest niezwykle zabytkowa -- powinieneś zamiast tego <a href="#" onclick="goto(\'bup\')">użyć bup</a>',
		"u_nowork": "wymaga Firefox 53+, Chrome 57+ lub iOS 11+",
		"tail_2old": "wymaga Firefox 105+, Chrome 71+ lub iOS 14.5+",
		"u_nodrop": 'ta przeglądarka jest za stara, nie wspiera przesyłania "przeciągnij i upuść"',
		"u_notdir": "to nie jest folder!\n\nta przeglądarka jest za stara\nspróbuj przeciągnąć i upuścić",
		"u_uri": "aby przeciągnąć i upuścić obrazy z innych okien przeglądarki,\nupuść je na duży przycisk przesyłania",
		"u_enpot": 'przełącz na <a href="#">lekki interfejs</a> (może zwiększyć prędkość przesyłania)',
		"u_depot": 'przełącz na <a href="#">ładny interfejs</a> (może zmniejszyć prędkośc przesyłania)',
		"u_gotpot": 'przełączanie na lekki interfejs w celu poprawy prędkości przesyłania,\n\nzawsze można przełączyć się na ładny interfejs!',
		"u_pott": "<p>pliki: &nbsp; <b>{0}</b> ukończonych, &nbsp; <b>{1}</b> nie powiodło się, &nbsp; <b>{2}</b> w trakcie, &nbsp; <b>{3}</b> oczekujących</p>",
		"u_ever": "podstawowe przesyłanie; up2k wymaga minimalnie przeglądarek:<br>Chrome 21 // Firefox 13 // Edge 12 // Opera 12 // Safari 5.1",
		"u_su2k": 'podstawowe przesyłanie; <a href="#" id="u2yea">up2k</a> jest lepszy',
		"u_uput": 'optymalizuj dla prędkości (pomijając spr. sum kontrolnych)',
		"u_ewrite": 'nie masz dostępu do zapisu (write) w tym folderze',
		"u_eread": 'nie masz dostępu do odczytu (read) tego folderu',
		"u_enoi": 'wyszukiwanie plików jest wyłączone w konfiguracji serwera',
		"u_enoow": "nadpisanie nie zadziała, wymagany dostęp do usuwania (delete)",
		"u_badf": '{0} (z {1}) plików zostało pominiętych, prawdopodobnie przez opcje dostępu systemu plików:\n\n',
		"u_blankf": '{0} (z {1}) plików jest pustych; przesłać mimo to?\n\n',
		"u_applef": '{0} (z {1}) plików może być niepożądane;\nNaciśnij <code>OK/Enter</code>, aby pominąć je (wypisane poniżej);\nNaciśnij <code>Anuluj/ESC</code>, by je przesłać mimo to:\n\n',
		"u_just1": '\nTa funkcja może działać lepiej z wybranym jednym plikiem',
		"u_ff_many": "na systemach <b>Linux / MacOS / Android,</b> ta ilośc plików <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>może</em> spowodować przymusowe zamknięcie przeglądarki Firefox</a>\nw takim przypadku, spróbuj ponownie (lub użyj Chrome'a).",
		"u_up_life": "Ten przesyłany plik zostanie usunięty z serwera\n{0} po zakończeniu przesyłania",
		"u_asku": 'prześlij {0} pliki(ów) do <code>{1}</code>',
		"u_unpt": "można cofnąć / usunąć ten przesłany plik za pomocą 🧯 w lewym górnym rogu",
		"u_bigtab": 'zaraz pokażę {0} plików\n\nta operacja może zawiesić twoją przeglądarkę, na pewno kontynuować?',
		"u_scan": 'Skanowanie plików...',
		"u_dirstuck": 'iterator katalogów utknął podczas próby dostępu poniższych {0} elementów, pominięto:',
		"u_etadone": 'Ukończono ({0}, {1} plików)',
		"u_etaprep": '(przygotowywanie do przesłania)',
		"u_hashdone": 'obliczono sumę kontrolną',
		"u_hashing": 'obliczanie sumy kontrolnej',
		"u_hs": 'nawiązywanie połączenia...',
		"u_started": "rozpoczęto przesyłanie; zobacz w [🚀]",
		"u_dupdefer": "duplikat; zostanie przetworzony na końcu",
		"u_actx": "kliknij ten napis, aby zapobiec spadkowi <br />wydajności po zmianie aktywnego okna/karty przeglądarki",
		"u_fixed": "OK!&nbsp; Naprawiono 👍",
		"u_cuerr": "nie udało się przesłać fragmentu {0} z {1};\nprawdopodobnie niegroźne, kontynuowanie\n\nplik: {2}",
		"u_cuerr2": "serwer odrzucił przesyłanie (kawałek {0} z {1});\nspróbuję ponownie później\n\nplik: {2}\n\nbłąd ",
		"u_ehstmp": "spróbuję ponownie; więcej informacji w prawym dolnym rogu",
		"u_ehsfin": "serwer odrzucił prośbę o zakończenie przesyłania; próbuję ponownie...",
		"u_ehssrch": "serwer odrzucił prośbę o wykonanie wyszukania; próbuję ponownie...",
		"u_ehsinit": "serwer odrzucił prośbę o rozpoczęcie przesyłania; próbuję ponownie...",
		"u_eneths": "błąd sieci podczas negocjacji warunków przesyłania; próbuję ponownie...",
		"u_enethd": "błąd sieci podczas sprawdzania istnienia celu; próbuję ponownie...",
		"u_cbusy": "oczekiwanie na ponowne zaufanie serwera po błędzie sieci...",
		"u_ehsdf": "brak miejsca na dysku serwera!\n\npróby będą ponawiane na wypadek\nzwolnienia wystarczająco dużo miejsca aby kontynuować",
		"u_emtleak1": "wygląda na to, że twoja przeglądarka może mieć wyciek pamięci;\n",
		"u_emtleak2": ' <a href="{0}">przejdź na HTTPS (zalecane)</a> lub ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'spróbuj:\n<ul><li>wciśnij <code>F5</code>, aby odświeżyć stronę</li><li>wyłącz przycisk &nbsp;<code>ww</code>&nbsp; w menu <code>⚙️ ustawienia</code></li><li>i spróbuj przesłać ponownie</li></ul>Prędkość przesyłania będzie niższa, ale cóż zrobisz.\nPrzepraszamy za problemu!\n\nPS: Chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">ma poprawkę tego błędu</a>.',
		"u_emtleakf": 'spróbuj:\n<ul><li>wciśnij <code>F5</code>, aby odświeżyć stronę</li><li>włącz tryb <code>🥔</code> (lekkiego interfejsu) w interfejsie przesyłania<li>i spróbuj przesłać ponownie</li></ul>\nPS: Firefox może kiedyś mieć <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">poprawkę tego błędu</a>',
		"u_s404": "nie znaleziono na serwerze",
		"u_expl": "wytłumacz",
		"u_maxconn": "większość przeglądarek ogranicza to do 6, ale Firefox pozwala zwiększyć tą wartość, ustawiając <code>connections-per-server</code> w <code>about:config</code>",
		"u_tu": '<p class="warn">UWAGA: tryb turbo włączony, <span>&nbsp;klient może nie wykryć i nie kontynuować niedokończonych przesłań; patrz wskazówka przycisku turbo</span></p>',
		"u_ts": '<p class="warn">UWAGA: tryb turbo włączony, <span>&nbsp;wyniki wyszukiwania mogą być niepoprawne; patrz wskazówka przycisku turbo</span></p>',
		"u_turbo_c": "tryb turbo jest wyłączony w konfiguracji serwera",
		"u_turbo_g": "wyłączanie trybu turbo, nie posiadasz dostępu\ndo listy katalogu w tym wolumenie",
		"u_life_cfg": 'autousuwanie po <input id="lifem" p="60" /> min (lub <input id="lifeh" p="3600" /> godz.)',
		"u_life_est": 'przesłany plik zostanie usunięty <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'ten folder wymaga\nmaks. czasu do usunięcia równego {0}',
		"u_unp_ok": 'unpost jest dozwolony przez {0}',
		"u_unp_ng": 'unpost NIE jest dozwolony',
		"ue_ro": 'dostęp tylko-do-odczytu\n\n',
		"ue_nl": 'nie jesteś zalogowany',
		"ue_la": 'zalogowano jako "{0}"',
		"ue_sr": 'jesteś w trybie wyszukiwania\n\nprzełącz się na tryb przesyłania, klikając lupę 🔎 (obok przycisku Szukaj), i spróbuj ponownie',
		"ue_ta": 'spróbuj przesłać ponownie, wszystko powinno być w porządku',
		"ue_ab": "ten plik już jest przesyłany do innego folderu, przesyłanie musi się zakończyć, zanim będzie mógł być on przesłany gdzie indziej.\n\nMożna przerwać pierwsze przesyłanie za pomocą 🧯 w lewym górnym rogu",
		"ur_1uo": "OK: Plik przesłany pomyślnie",
		"ur_auo": "OK: Wszystkie ({0}) pliki zostały przesłane pomyślnie",
		"ur_1so": "OK: Znaleziono plik na serwerze",
		"ur_aso": "OK: Znaleziono wszystkie ({0}) pliki na serwerze",
		"ur_1un": "Przesyłanie nie powiodło się",
		"ur_aun": "Wszystkie ({0}) przesłania nie powiodły się",
		"ur_1sn": "NIE znaleziono pliku na serwerze",
		"ur_asn": "NIE znaleziono {0} plików na serwerze",
		"ur_um": "Zakończono;\n{0} przesłań OK,\n{1} przesłań nie powiodło się",
		"ur_sm": "Zakończono;\nznaleziono {0} pliki(ów),\nnie znaleziono {1} pliki(ów) na serwerze",

		"lang_set": "odśwież stronę (F5), aby zastosować zmianę.",
	},
	"por": {
		"tt": "Português",

		"cols": {
			"c": "botões de ação",
			"dur": "duração",
			"q": "qualidade / bitrate",
			"Ac": "codec de áudio",
			"Vc": "codec de vídeo",
			"Fmt": "formato / contêiner",
			"Ahash": "checksum de áudio",
			"Vhash": "checksum de vídeo",
			"Res": "resolução",
			"T": "tipo de arquivo",
			"aq": "qualidade / bitrate de áudio",
			"vq": "qualidade / bitrate de vídeo",
			"pixfmt": "subamostragem / estrutura de pixel",
			"resw": "resolução horizontal",
			"resh": "resolução vertical",
			"chs": "canais de áudio",
			"hz": "taxa de amostragem"
		},

		"hks": [
			[
				"diversos",
				["ESC", "fechar várias coisas"],

				"gerenciador de arquivos",
				["G", "alternar entre visualização de lista / grade"],
				["T", "alternar entre miniaturas / ícones"],
				["⇧ A/D", "tamanho da miniatura"],
				["ctrl-K", "excluir selecionados"],
				["ctrl-X", "recortar seleção para a área de transferência"],
				["ctrl-C", "copiar seleção para a área de transferência"],
				["ctrl-V", "colar (mover/copiar) aqui"],
				["Y", "baixar selecionado"],
				["F2", "renomear selecionado"],

				"seleção de lista de arquivos",
				["espaço", "alternar seleção de arquivo"],
				["↑/↓", "mover cursor de seleção"],
				["ctrl ↑/↓", "mover cursor e visualização"],
				["⇧ ↑/↓", "selecionar arquivo anterior/próximo"],
				["ctrl-A", "selecionar todos os arquivos / pastas"],
			], [
				"navegação",
				["B", "alternar entre breadcrumbs / painel de navegação"],
				["I/K", "pasta anterior/próxima"],
				["M", "pasta pai (ou desexpandir a atual)"],
				["V", "alternar entre pastas / arquivos de texto no painel de navegação"],
				["A/D", "tamanho do painel de navegação"],
			], [
				"reprodutor de áudio",
				["J/L", "música anterior/próxima"],
				["U/O", "pular 10 segundos para trás/frente"],
				["0..9", "pular para 0%..90%"],
				["P", "reproduzir/pausar (também inicia)"],
				["S", "selecionar a música que está tocando"],
				["Y", "baixar música"],
			], [
				"visualizador de imagens",
				["J/L, ←/→", "imagem anterior/próxima"],
				["Home/End", "primeira/última imagem"],
				["F", "tela cheia"],
				["R", "girar no sentido horário"],
				["⇧ R", "girar no sentido anti-horário"],
				["S", "selecionar imagem"],
				["Y", "baixar imagem"],
			], [
				"reprodutor de vídeo",
				["U/O", "pular 10 segundos para trás/frente"],
				["P/K/Espaço", "reproduzir/pausar"],
				["C", "continuar reproduzindo o próximo"],
				["V", "loop"],
				["M", "mudo"],
				["[ e ]", "definir intervalo de loop"],
			], [
				"visualizador de arquivos de texto",
				["I/K", "arquivo anterior/próximo"],
				["M", "fechar arquivo de texto"],
				["E", "editar arquivo de texto"],
				["S", "selecionar arquivo (para recortar/copiar/renomear)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Cancelar",

		"enable": "Ativar",
		"danger": "PERIGO",
		"clipped": "copiado para a área de transferência",

		"ht_s1": "segundo",
		"ht_s2": "segundos",
		"ht_m1": "minuto",
		"ht_m2": "minutos",
		"ht_h1": "hora",
		"ht_h2": "horas",
		"ht_d1": "dia",
		"ht_d2": "dias",
		"ht_and": " e ",

		"goh": "painel de controle",
		"gop": 'pai anterior">anterior',
		"gou": 'pasta pai">acima',
		"gon": 'próxima pasta">próximo',
		"logout": "Sair ",
		"login": "Fazer login",
		"access": " acesso",
		"ot_close": "fechar submenu",
		"ot_search": "procurar arquivos por atributos, caminho / nome, tags de música ou qualquer combinação deles$N$N&lt;code&gt;foo bar&lt;/code&gt; = deve conter ambos «foo» e «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = deve conter «foo» mas não «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = começar com «yana» e ser um arquivo «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = conter exatamente «try unite»$N$No formato de data é iso-8601, como$N&lt;code&gt;2009-12-31&lt;/code&gt; ou &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "despublicar: excluir seus uploads recentes, ou abortar os que não foram concluídos",
		"ot_bup": "bup: uploader básico, até suporta netscape 4.0",
		"ot_mkdir": "mkdir: criar um novo diretório",
		"ot_md": "new-md: criar um novo documento markdown",
		"ot_msg": "msg: enviar uma mensagem para o log do servidor",
		"ot_mp": "opções do reprodutor de mídia",
		"ot_cfg": "opções de configuração",
		"ot_u2i": 'up2k: fazer upload de arquivos (se você tiver acesso de escrita) ou alternar para o modo de busca para ver se eles já existem em algum lugar no servidor$N$Nuploads são reiniciáveis, multithread, e os carimbos de data/hora dos arquivos são preservados, mas usa mais CPU que [🎈]&nbsp; (o uploader básico)<br /><br />durante os uploads, este ícone se torna um indicador de progresso!',
		"ot_u2w": 'up2k: fazer upload de arquivos com suporte a retomada (feche seu navegador e solte os mesmos arquivos mais tarde)$N$Nmultithread, e os carimbos de data/hora dos arquivos são preservados, mas usa mais CPU que [🎈]&nbsp; (o uploader básico)<br /><br />durante os uploads, este ícone se torna um indicador de progresso!',
		"ot_noie": 'Por favor, use Chrome / Firefox / Edge',

		"ab_mkdir": "criar diretório",
		"ab_mkdoc": "novo documento markdown",
		"ab_msg": "enviar msg para o log do srv",

		"ay_path": "pular para pastas",
		"ay_files": "pular para arquivos",

		"wt_ren": "renomear itens selecionados$NHotkey: F2",
		"wt_del": "excluir itens selecionados$NHotkey: ctrl-K",
		"wt_cut": "recortar itens selecionados &lt;small&gt;(depois colar em outro lugar)&lt;/small&gt;$NHotkey: ctrl-X",
		"wt_cpy": "copiar itens selecionados para a área de transferência$N(para colá-los em outro lugar)$NHotkey: ctrl-C",
		"wt_pst": "colar uma seleção previamente recortada / copiada$NHotkey: ctrl-V",
		"wt_selall": "selecionar todos os arquivos$NHotkey: ctrl-A (quando o arquivo estiver em foco)",
		"wt_selinv": "inverter seleção",
		"wt_zip1": "baixar esta pasta como um arquivo compactado",
		"wt_selzip": "baixar seleção como um arquivo compactado",
		"wt_seldl": "baixar seleção como arquivos separados$NHotkey: Y",
		"wt_npirc": "copiar informações da faixa em formato irc",
		"wt_nptxt": "copiar informações da faixa em texto simples",
		"wt_m3ua": "adicionar à playlist m3u (clique em <code>📻copiar</code> depois)",
		"wt_m3uc": "copiar playlist m3u para a área de transferência",
		"wt_grid": "alternar entre visualização de grade / lista$NHotkey: G",
		"wt_prev": "faixa anterior$NHotkey: J",
		"wt_play": "reproduzir / pausar$NHotkey: P",
		"wt_next": "próxima faixa$NHotkey: L",

		"ul_par": "uploads paralelos:",
		"ut_rand": "randomizar nomes de arquivos",
		"ut_u2ts": "copiar o carimbo de data/hora de última modificação$Ndo seu sistema de arquivos para o servidor\">📅",
		"ut_ow": "substituir arquivos existentes no servidor?$N🛡️: nunca (irá gerar um novo nome de arquivo em vez disso)$N🕒: substituir se o arquivo no servidor for mais antigo que o seu$N♻️: sempre substituir se os arquivos forem diferentes",
		"ut_mt": "continuar a fazer o hash de outros arquivos enquanto faz upload$N$Ntalvez desativar se sua CPU ou HDD for um gargalo",
		"ut_ask": 'pedir confirmação antes do upload começar">💭',
		"ut_pot": "melhorar a velocidade de upload em dispositivos lentos$Ntornando a UI menos complexa",
		"ut_srch": "não fazer upload, em vez disso verificar se os arquivos já$N existem no servidor (irá escanear todas as pastas que você pode ler)",
		"ut_par": "pausar uploads definindo para 0$N$naumentar se sua conexão for lenta / alta latência$N$nmanter em 1 em LAN ou se o HDD do servidor for um gargalo",
		"ul_btn": "soltar arquivos / pastas<br>aqui (ou clique em mim)",
		"ul_btnu": "U P L O A D",
		"ul_btns": "B U S C A R",

		"ul_hash": "hash",
		"ul_send": "enviar",
		"ul_done": "feito",
		"ul_idle1": "nenhum upload está na fila ainda",
		"ut_etah": "velocidade média de &lt;em&gt;hash&lt;/em&gt;, e tempo estimado até o fim",
		"ut_etau": "velocidade média de &lt;em&gt;upload&lt;/em&gt; e tempo estimado até o fim",
		"ut_etat": "velocidade média &lt;em&gt;total&lt;/em&gt; e tempo estimado até o fim",

		"uct_ok": "concluído com sucesso",
		"uct_ng": "ruim: falhou / rejeitado / não encontrado",
		"uct_done": "ok e ruim combinados",
		"uct_bz": "fazendo hash ou upload",
		"uct_q": "ocioso, pendente",

		"utl_name": "nome do arquivo",
		"utl_ulist": "lista",
		"utl_ucopy": "copiar",
		"utl_links": "links",
		"utl_stat": "status",
		"utl_prog": "progresso",

		// mantenha curto:
		"utl_404": "404",
		"utl_err": "ERRO",
		"utl_oserr": "Erro-SO",
		"utl_found": "encontrado",
		"utl_defer": "adiar",
		"utl_yolo": "YOLO",
		"utl_done": "feito",

		"ul_flagblk": "os arquivos foram adicionados à fila</b><br>no entanto, há um up2k ocupado em outra aba do navegador,<br>então esperando que ele termine primeiro",
		"ul_btnlk": "a configuração do servidor bloqueou este interruptor neste estado",

		"udt_up": "Upload",
		"udt_srch": "Buscar",
		"udt_drop": "solte aqui",

		"u_nav_m": '<h6>certo, o que você tem?</h6><code>Enter</code> = Arquivos (um ou mais)\n<code>ESC</code> = Uma pasta (incluindo subpastas)',
		"u_nav_b": '<a href="#" id="modal-ok">Arquivos</a><a href="#" id="modal-ng">Uma pasta</a>',

		"cl_opts": "interruptores",
		"cl_themes": "tema",
		"cl_langs": "idioma",
		"cl_ziptype": "download de pasta",
		"cl_uopts": "interruptores up2k",
		"cl_favico": "favicon",
		"cl_bigdir": "grandes dirs",
		"cl_hsort": "#sort",
		"cl_keytype": "notação de tecla",
		"cl_hiddenc": "colunas ocultas",
		"cl_hidec": "ocultar",
		"cl_reset": "resetar",
		"cl_hpick": "toque nos cabeçalhos das colunas para ocultá-los na tabela abaixo",
		"cl_hcancel": "ocultar coluna abortado",

		"ct_grid": '田 a grade',
		"ct_ttips": '◔ ◡ ◔">ℹ️ dicas de ferramentas',
		"ct_thumb": 'na visualização de grade, alternar entre ícones ou miniaturas$NHotkey: T">🖼️ miniaturas',
		"ct_csel": 'usar CTRL e SHIFT para seleção de arquivo na visualização de grade">sel',
		"ct_ihop": 'quando o visualizador de imagens for fechado, rolar para o último arquivo visualizado">g⮯',
		"ct_dots": 'mostrar arquivos ocultos (se o servidor permitir)">dotfiles',
		"ct_qdel": 'ao excluir arquivos, pedir confirmação apenas uma vez">qdel',
		"ct_dir1st": 'ordenar pastas antes de arquivos">📁 primeiro',
		"ct_nsort": 'ordem natural (para nomes de arquivos com dígitos iniciais)">nsort',
		"ct_utc": 'mostrar todas as datas/horas em UTC">UTC',
		"ct_readme": 'mostrar README.md nas listas de pastas">📜 readme',
		"ct_idxh": 'mostrar index.html em vez de lista de pastas">htm',
		"ct_sbars": 'mostrar barras de rolagem">⟊',

		"cut_umod": "se um arquivo já existe no servidor, atualizar o carimbo de data/hora de última modificação do servidor para corresponder ao seu arquivo local (requer permissões de escrita+exclusão)\">re📅",

		"cut_turbo": "o botão yolo, você provavelmente NÃO quer habilitar isso:$N$Nuse isto se você estava fazendo upload de uma enorme quantidade de arquivos e teve que reiniciar por algum motivo, e quer continuar o upload o mais rápido possível$N$Nisto substitui a verificação de hash por uma simples <em>&quot;este arquivo tem o mesmo tamanho no servidor?&quot;</em> então se o conteúdo do arquivo for diferente ele NÃO será enviado$N$Nvocê deve desativar isso quando o upload estiver concluído, e então &quot;enviar&quot; os mesmos arquivos novamente para permitir que o cliente os verifique\">turbo",

		"cut_datechk": "não tem efeito a menos que o botão turbo esteja ativado$N$Nreduz o fator yolo por uma pequena quantidade; verifica se os carimbos de data/hora dos arquivos no servidor correspondem aos seus$N$ndeve <em>teoricamente</em> pegar a maioria dos uploads incompletos / corrompidos, mas não é um substituto para fazer uma verificação com o turbo desativado depois\">date-chk",

		"cut_u2sz": "tamanho (em MiB) de cada bloco de upload; valores grandes voam melhor pelo atlântico. Tente valores baixos em conexões muito não confiáveis",

		"cut_flag": "garantir que apenas uma aba esteja fazendo upload por vez $N -- outras abas devem ter isso ativado também $N -- só afeta abas no mesmo domínio",

		"cut_az": "enviar arquivos em ordem alfabética, em vez de o menor primeiro$N$na ordem alfabética pode tornar mais fácil de verificar se algo deu errado no servidor, mas torna o upload um pouco mais lento em fibra / LAN",

		"cut_nag": "notificação do SO quando o upload for concluído$N(somente se o navegador ou aba não estiver ativo)",
		"cut_sfx": "alerta audível quando o upload for concluído$N(somente se o navegador ou aba não estiver ativo)",

		"cut_mt": "usar multithreading para acelerar o hash de arquivos$N$nisto usa web-workers e requer$Nmais RAM (até 512 MiB extras)$N$ntorna https 30% mais rápido, http 4.5x mais rápido\">mt",

		"cut_wasm": "usar wasm em vez do hasher embutido do navegador; melhora a velocidade em navegadores baseados em chrome mas aumenta a carga da CPU, e muitas versões antigas do chrome têm bugs que fazem o navegador consumir toda a RAM e travar se isso for ativado\">wasm",

		"cft_text": "texto do favicon (deixe em branco e atualize para desativar)",
		"cft_fg": "cor do primeiro plano",
		"cft_bg": "cor do fundo",

		"cdt_lim": "número máximo de arquivos para mostrar em uma pasta",
		"cdt_ask": "ao rolar para o final,$nem vez de carregar mais arquivos,$nperguntar o que fazer",
		"cdt_hsort": "quantas regras de ordenação (&lt;code&gt;,sorthref&lt;/code&gt;) incluir em URLs de mídia. Definir isso para 0 também ignorará as regras de ordenação incluídas em links de mídia quando você clicar neles",

		"tt_entree": "mostrar painel de navegação (árvore de diretórios)$NHotkey: B",
		"tt_detree": "mostrar breadcrumbs$NHotkey: B",
		"tt_visdir": "rolar para a pasta selecionada",
		"tt_ftree": "alternar entre árvore de pastas / arquivos de texto$NHotkey: V",
		"tt_pdock": "mostrar pastas pai em um painel acoplado no topo",
		"tt_dynt": "crescer automaticamente à medida que a árvore se expande",
		"tt_wrap": "quebra de linha",
		"tt_hover": "revelar linhas transbordando ao passar o mouse$N( quebra a rolagem a menos que o cursor do mouse $N&nbsp; esteja na margem esquerda )",

		"ml_pmode": "ao final da pasta...",
		"ml_btns": "comandos",
		"ml_tcode": "transcodificar",
		"ml_tcode2": "transcodificar para",
		"ml_tint": "matiz",
		"ml_eq": "equalizador de áudio",
		"ml_drc": "compressor de faixa dinâmica",

		"mt_loop": "loop/repetir uma música\">🔁",
		"mt_one": "parar depois de uma música\">1️⃣",
		"mt_shuf": "embaralhar as músicas em cada pasta\">🔀",
		"mt_aplay": "reproduzir automaticamente se houver um ID de música no link que você clicou para acessar o servidor$N$ndesativar isso também impedirá que a URL da página seja atualizada com IDs de música ao tocar música, para evitar a reprodução automática se essas configurações forem perdidas mas a URL permanecer\">a▶",
		"mt_preload": "começar a carregar a próxima música perto do final para uma reprodução sem interrupções\">preload",
		"mt_prescan": "ir para a próxima pasta antes que a última música$Ntermine, mantendo o navegador feliz$Npara que ele não pare a reprodução\">nav",
		"mt_fullpre": "tentar pré-carregar a música inteira;$N✅ ativar em conexões <b>não confiáveis</b>,$N❌ <b>desativar</b> em conexões lentas provavelmente\">full",
		"mt_fau": "em telefones, evitar que a música pare se a próxima música não pré-carregar rápido o suficiente (pode fazer as tags aparecerem com falhas)\">☕️",
		"mt_waves": "barra de busca de forma de onda:$Nmostrar amplitude de áudio no scrubber\">~s",
		"mt_npclip": "mostrar botões para copiar a música que está tocando para a área de transferência\">/np",
		"mt_m3u_c": "mostrar botões para copiar as$Nmúsicas selecionadas como entradas de playlist m3u8 para a área de transferência\">📻",
		"mt_octl": "integração com o SO (atalhos de mídia / osd)\">os-ctl",
		"mt_oseek": "permitir busca através da integração com o SO$N$nnota: em alguns dispositivos (iPhones),$nisto substitui o botão de próxima música\">seek",
		"mt_oscv": "mostrar capa do álbum no osd\">art",
		"mt_follow": "manter a faixa que está tocando rolando à vista\">🎯",
		"mt_compact": "controles compactos\">⟎",
		"mt_uncache": "limpar cache &nbsp;(tente isso se seu navegador armazenou em cache$Numa cópia quebrada de uma música e se recusa a tocar)\">uncache",
		"mt_mloop": "loop na pasta aberta\">🔁 loop",
		"mt_mnext": "carregar a próxima pasta e continuar\">📂 próximo",
		"mt_mstop": "parar reprodução\">⏸ parar",
		"mt_cflac": "converter flac / wav para {0}\">flac",
		"mt_caac": "converter aac / m4a para {0}\">aac",
		"mt_coth": "converter todos os outros (não mp3) para {0}\">oth",
		"mt_c2opus": "melhor escolha para desktops, laptops, android\">opus",
		"mt_c2owa": "opus-weba, para iOS 17.5 e mais recentes\">owa",
		"mt_c2caf": "opus-caf, para iOS 11 a 17\">caf",
		"mt_c2mp3": "use isso em dispositivos muito antigos\">mp3",
		"mt_c2flac": "melhor qualidade de som, mas downloads enormes\">flac",
		"mt_c2wav": "reprodução não comprimida (ainda maior)\">wav",
		"mt_c2ok": "legal, boa escolha",
		"mt_c2nd": "esse não é o formato de saída recomendado para o seu dispositivo, mas tudo bem",
		"mt_c2ng": "seu dispositivo não parece suportar este formato de saída, mas vamos tentar mesmo assim",
		"mt_xowa": "existem bugs no iOS que impedem a reprodução em segundo plano usando este formato; por favor, use caf ou mp3 em vez disso",
		"mt_tint": "nível de fundo (0-100) na barra de busca$Npara tornar o buffer menos distrativo",
		"mt_eq": "ativa o equalizador e o controle de ganho;$N$nimpulsão &lt;code&gt;0&lt;/code&gt; = volume padrão de 100% (não modificado)$N$nlargura &lt;code&gt;1 &nbsp;&lt;/code&gt; = estéreo padrão (não modificado)$nlargura &lt;code&gt;0.5&lt;/code&gt; = 50% de crossfeed esquerda-direita$nlargura &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$nimpulsão &lt;code&gt;-0.8&lt;/code&gt; & largura &lt;code&gt;10&lt;/code&gt; = remoção de vocal :^)$N$natvar o equalizador torna os álbuns sem interrupções totalmente sem interrupções, então deixe-o ligado com todos os valores em zero (exceto largura = 1) se você se importa com isso",
		"mt_drc": "ativa o compressor de faixa dinâmica (nivelador de volume / brickwaller); também ativará o EQ para equilibrar o spaghetti, então defina todos os campos EQ exceto 'width' para 0 se você não quiser$N$nabaixa o volume do áudio acima do THRESHOLD dB; para cada RATIO dB após o THRESHOLD há 1 dB de saída, então os valores padrão de tresh -24 e ratio 12 significam que nunca deve ficar mais alto que -22 dB e é seguro aumentar o impulso do equalizador para 0.8, ou até 1.8 com ATK 0 e um enorme RLS como 90 (só funciona no firefox; RLS é no máximo 1 em outros navegadores)$N$n(veja a wikipedia, eles explicam muito melhor)",

		"mb_play": "reproduzir",
		"mm_hashplay": "reproduzir este arquivo de áudio?",
		"mm_m3u": "pressione <code>Enter/OK</code> para Reproduzir\npressione <code>ESC/Cancelar</code> para Editar",
		"mp_breq": "precisa do firefox 82+ ou chrome 73+ ou iOS 15+",
		"mm_bload": "carregando...",
		"mm_bconv": "convertendo para {0}, por favor, espere...",
		"mm_opusen": "seu navegador não pode reproduzir arquivos aac / m4a;\na transcodificação para opus agora está ativada",
		"mm_playerr": "reprodução falhou: ",
		"mm_eabrt": "A tentativa de reprodução foi cancelada",
		"mm_enet": "Sua conexão de internet está instável",
		"mm_edec": "Este arquivo está supostamente corrompido??",
		"mm_esupp": "Seu navegador não entende este formato de áudio",
		"mm_eunk": "Erro Desconhecido",
		"mm_e404": "Não foi possível reproduzir áudio; erro 404: Arquivo não encontrado.",
		"mm_e403": "Não foi possível reproduzir áudio; erro 403: Acesso negado.\n\nTente pressionar F5 para recarregar, talvez você tenha saído da conta",
		"mm_e500": "Não foi possível reproduzir áudio; erro 500: Verifique os logs do servidor.",
		"mm_e5xx": "Não foi possível reproduzir áudio; erro do servidor ",
		"mm_nof": "não encontrando mais arquivos de áudio por perto",
		"mm_prescan": "Procurando música para tocar a seguir...",
		"mm_scank": "Encontrei a próxima música:",
		"mm_uncache": "cache limpo; todas as músicas serão baixadas novamente na próxima reprodução",
		"mm_hnf": "essa música não existe mais",

		"im_hnf": "essa imagem não existe mais",

		"f_empty": 'esta pasta está vazia',
		"f_chide": 'isso irá ocultar a coluna «{0}»\n\nvocê pode reexibir as colunas na aba de configurações',
		"f_bigtxt": "este arquivo tem {0} MiB de tamanho -- realmente ver como texto?",
		"f_bigtxt2": "ver apenas o final do arquivo em vez disso? isso também ativará o acompanhamento/tailing, mostrando linhas de texto recém-adicionadas em tempo real",
		"fbd_more": '<div id="blazy">mostrando <code>{0}</code> de <code>{1}</code> arquivos; <a href="#" id="bd_more">mostrar {2}</a> ou <a href="#" id="bd_all">mostrar todos</a></div>',
		"fbd_all": '<div id="blazy">mostrando <code>{0}</code> de <code>{1}</code> arquivos; <a href="#" id="bd_all">mostrar todos</a></div>',
		"f_anota": "apenas {0} dos {1} itens foram selecionados;\npara selecionar a pasta inteira, primeiro role para o final",

		"f_dls": 'os links de arquivo na pasta atual foram\nalterados para links de download',

		"f_partial": "Para baixar com segurança um arquivo que está sendo enviado, por favor, clique no arquivo que tem o mesmo nome, mas sem a extensão <code>.PARTIAL</code>. Por favor, pressione CANCELAR ou Escape para fazer isso.\n\nPressionar OK / Enter irá ignorar este aviso e continuar baixando o arquivo temporário <code>.PARTIAL</code>, o que quase certamente lhe dará dados corrompidos.",

		"ft_paste": "colar {0} itens$NHotkey: ctrl-V",
		"fr_eperm": 'não é possível renomear:\nvocê não tem permissão de “mover” nesta pasta',
		"fd_eperm": 'não é possível excluir:\nvocê não tem permissão de “excluir” nesta pasta',
		"fc_eperm": 'não é possível recortar:\nvocê não tem permissão de “mover” nesta pasta',
		"fp_eperm": 'não é possível colar:\nvocê não tem permissão de “escrever” nesta pasta',
		"fr_emore": "selecione pelo menos um item para renomear",
		"fd_emore": "selecione pelo menos um item para excluir",
		"fc_emore": "selecione pelo menos um item para recortar",
		"fcp_emore": "selecione pelo menos um item para copiar para a área de transferência",

		"fs_sc": "compartilhar a pasta em que você está",
		"fs_ss": "compartilhar os arquivos selecionados",
		"fs_just1d": "você não pode selecionar mais de uma pasta,\nou misturar arquivos e pastas em uma seleção",
		"fs_abrt": "❌ abortar",
		"fs_rand": "🎲 nome aleatório",
		"fs_go": "✅ criar compartilhamento",
		"fs_name": "nome",
		"fs_src": "fonte",
		"fs_pwd": "senha",
		"fs_exp": "expira",
		"fs_tmin": "min",
		"fs_thrs": "horas",
		"fs_tdays": "dias",
		"fs_never": "eterno",
		"fs_pname": "nome do link opcional; será aleatório se em branco",
		"fs_tsrc": "o arquivo ou pasta a ser compartilhado",
		"fs_ppwd": "senha opcional",
		"fs_w8": "criando compartilhamento...",
		"fs_ok": "pressione <code>Enter/OK</code> para Copiar para a Área de Transferência\npressione <code>ESC/Cancelar</code> para Fechar",

		"frt_dec": "pode consertar alguns casos de nomes de arquivos quebrados\">url-decode",
		"frt_rst": "resetar nomes de arquivos modificados de volta para os originais\">↺ resetar",
		"frt_abrt": "abortar e fechar esta janela\">❌ cancelar",
		"frb_apply": "APLICAR RENOMEAÇÃO",
		"fr_adv": "renomeação em lote / metadados / padrão\">avançado",
		"fr_case": "regex sensível a maiúsculas e minúsculas\">case",
		"fr_win": "nomes seguros para windows; substituir <code>&lt;&gt;:&quot;\\|?*</code> por caracteres japoneses de largura total\">win",
		"fr_slash": "substituir <code>/</code> por um caractere que não cause a criação de novas pastas\">no /",
		"fr_re": "padrão de busca regex para aplicar aos nomes de arquivos originais; grupos de captura podem ser referenciados no campo de formato abaixo como &lt;code&gt;(1)&lt;/code&gt; e &lt;code&gt;(2)&lt;/code&gt; e assim por diante",
		"fr_fmt": "inspirado por foobar2000:$N&lt;code&gt;(título)&lt;/code&gt; é substituído pelo título da música,$N&lt;code&gt;[(artista) - ](título)&lt;/code&gt; pula esta parte se o artista estiver em branco$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; preenche o número da faixa com 2 dígitos",
		"fr_pdel": "excluir",
		"fr_pnew": "salvar como",
		"fr_pname": "forneça um nome para seu novo preset",
		"fr_aborted": "abortado",
		"fr_lold": "nome antigo",
		"fr_lnew": "novo nome",
		"fr_tags": "tags para os arquivos selecionados (somente leitura, apenas para referência):",
		"fr_busy": "renomeando {0} itens...\n\n{1}",
		"fr_efail": "renomeação falhou:\n",
		"fr_nchg": "{0} dos novos nomes foram alterados devido a <code>win</code> e/ou <code>no /</code>\n\nOK para continuar com estes novos nomes alterados?",

		"fd_ok": "exclusão OK",
		"fd_err": "exclusão falhou:\n",
		"fd_none": "nada foi excluído; talvez bloqueado pela configuração do servidor (xbd)?",
		"fd_busy": "excluindo {0} itens...\n\n{1}",
		"fd_warn1": "EXCLUIR estes {0} itens?",
		"fd_warn2": "<b>Última chance!</b> Não há como desfazer. Excluir?",

		"fc_ok": "recortar {0} itens",
		"fc_warn": 'recortar {0} itens\n\nmas: apenas <b>esta</b> aba do navegador pode colá-los\n(já que a seleção é tão absolutamente massiva)',

		"fcc_ok": "copiado {0} itens para a área de transferência",
		"fcc_warn": 'copiado {0} itens para a área de transferência\n\nmas: apenas <b>esta</b> aba do navegador pode colá-los\n(já que a seleção é tão absolutamente massiva)',

		"fp_apply": "usar estes nomes",
		"fp_ecut": "primeiro recorte ou copie alguns arquivos / pastas para colar / mover\n\nnota: você pode recortar / colar entre abas diferentes do navegador",
		"fp_ename": "{0} itens não podem ser movidos para cá porque os nomes já estão em uso. Dê a eles novos nomes abaixo para continuar, ou deixe o nome em branco para pular:",
		"fcp_ename": "{0} itens não podem ser copiados para cá porque os nomes já estão em uso. Dê a eles novos nomes abaixo para continuar, ou deixe o nome em branco para pular:",
		"fp_emore": "ainda há algumas colisões de nome de arquivo para consertar",
		"fp_ok": "movimento OK",
		"fcp_ok": "cópia OK",
		"fp_busy": "movendo {0} itens...\n\n{1}",
		"fcp_busy": "copiando {0} itens...\n\n{1}",
		"fp_abrt": "abortando...",
		"fp_err": "movimento falhou:\n",
		"fcp_err": "cópia falhou:\n",
		"fp_confirm": "mover estes {0} itens para cá?",
		"fcp_confirm": "copiar estes {0} itens para cá?",
		"fp_etab": 'falha ao ler a área de transferência de outra aba do navegador',
		"fp_name": "enviando um arquivo do seu dispositivo. Dê-lhe um nome:",
		"fp_both_m": '<h6>escolha o que colar</h6><code>Enter</code> = Mover {0} arquivos de «{1}»\n<code>ESC</code> = Enviar {2} arquivos do seu dispositivo',
		"fcp_both_m": '<h6>escolha o que colar</h6><code>Enter</code> = Copiar {0} arquivos de «{1}»\n<code>ESC</code> = Enviar {2} arquivos do seu dispositivo',
		"fp_both_b": '<a href="#" id="modal-ok">Mover</a><a href="#" id="modal-ng">Enviar</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Copiar</a><a href="#" id="modal-ng">Enviar</a>',

		"mk_noname": "digite um nome no campo de texto à esquerda antes de fazer isso :p",

		"tv_load": "Carregando documento de texto:\n\n{0}\n\n{1}% ({2} de {3} MiB carregados)",
		"tv_xe1": "não foi possível carregar o arquivo de texto:\n\nerro ",
		"tv_xe2": "404, arquivo não encontrado",
		"tv_lst": "lista de arquivos de texto em",
		"tvt_close": "voltar para a visualização da pasta$NHotkey: M (ou Esc)\">❌ fechar",
		"tvt_dl": "baixar este arquivo$NHotkey: Y\">💾 baixar",
		"tvt_prev": "mostrar documento anterior$NHotkey: i\">⬆ anterior",
		"tvt_next": "mostrar próximo documento$NHotkey: K\">⬇ próximo",
		"tvt_sel": "selecionar arquivo &nbsp; ( para recortar / copiar / excluir / ... )$NHotkey: S\">sel",
		"tvt_edit": "abrir arquivo no editor de texto$NHotkey: E\">✏️ editar",
		"tvt_tail": "monitorar arquivo para alterações; mostrar novas linhas em tempo real\">📡 seguir",
		"tvt_wrap": "quebra de linha\">↵",
		"tvt_atail": "fixar rolagem no final da página\">⚓",
		"tvt_ctail": "decodificar cores do terminal (códigos de escape ansi)\">🌈",
		"tvt_ntail": "limite de rolagem para trás (quantos bytes de texto manter carregados)",

		"m3u_add1": "música adicionada à playlist m3u",
		"m3u_addn": "{0} músicas adicionadas à playlist m3u",
		"m3u_clip": "playlist m3u agora copiada para a área de transferência\n\nvocê deve criar um novo arquivo de texto chamado something.m3u e colar a playlist nesse documento; isso a tornará reproduzível",

		"gt_vau": "não mostrar vídeos, apenas tocar o áudio\">🎧",
		"gt_msel": "ativar seleção de arquivo; ctrl-clique em um arquivo para substituir$N$n&lt;em&gt;quando ativo: clique duas vezes em um arquivo / pasta para abri-lo&&gt;t;/em&gt;$N$nHotkey: S\">multisseleção",
		"gt_crop": "cortar miniaturas ao centro\">cortar",
		"gt_3x": "miniaturas de alta resolução\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "picar",
		"gt_sort": "ordenar por",
		"gt_name": "nome",
		"gt_sz": "tamanho",
		"gt_ts": "data",
		"gt_ext": "tipo",
		"gt_c1": "truncar nomes de arquivos mais (mostrar menos)",
		"gt_c2": "truncar nomes de arquivos menos (mostrar mais)",

		"sm_w8": "buscando...",
		"sm_prev": "os resultados da busca abaixo são de uma consulta anterior:\n  ",
		"sl_close": "fechar resultados da busca",
		"sl_hits": "mostrando {0} resultados",
		"sl_moar": "carregar mais",

		"s_sz": "tamanho",
		"s_dt": "data",
		"s_rd": "caminho",
		"s_fn": "nome",
		"s_ta": "tags",
		"s_ua": "up@",
		"s_ad": "adv.",
		"s_s1": "MiB mínimo",
		"s_s2": "MiB máximo",
		"s_d1": "iso8601 min.",
		"s_d2": "iso8601 max.",
		"s_u1": "enviado depois de",
		"s_u2": "e/ou antes de",
		"s_r1": "caminho contém &nbsp; (separado por espaço)",
		"s_f1": "nome contém &nbsp; (negar com -nope)",
		"s_t1": "tags contém &nbsp; (^=início, fim=$)",
		"s_a1": "propriedades de metadados específicas",

		"md_eshow": "não é possível renderizar ",
		"md_off": "[📜<em>readme</em>] desativado em [⚙️] -- documento oculto",

		"badreply": "Falha ao analisar a resposta do servidor",

		"xhr403": "403: Acesso negado\n\ntente pressionar F5, talvez você tenha saído da conta",
		"xhr0": "desconhecido (provavelmente perdeu a conexão com o servidor, ou o servidor está offline)",
		"cf_ok": "desculpe por isso -- a proteção DD" + "oS foi ativada\n\nas coisas devem ser retomadas em cerca de 30 segundos\n\nse nada acontecer, pressione F5 para recarregar a página",
		"tl_xe1": "não foi possível listar as subpastas:\n\nerro ",
		"tl_xe2": "404: Pasta não encontrada",
		"fl_xe1": "não foi possível listar os arquivos na pasta:\n\nerro ",
		"fl_xe2": "404: Pasta não encontrada",
		"fd_xe1": "não foi possível criar a subpasta:\n\nerro ",
		"fd_xe2": "404: Pasta pai não encontrada",
		"fsm_xe1": "não foi possível enviar a mensagem:\n\nerro ",
		"fsm_xe2": "404: Pasta pai não encontrada",
		"fu_xe1": "falha ao carregar a lista de despublicação do servidor:\n\nerro ",
		"fu_xe2": "404: Arquivo não encontrado??",

		"fz_tar": "arquivo gnu-tar não comprimido (linux / mac)",
		"fz_pax": "tar de formato pax não comprimido (mais lento)",
		"fz_targz": "gnu-tar com compressão gzip nível 3$N$nisto é geralmente muito lento, então$nuse tar não comprimido em vez disso",
		"fz_tarxz": "gnu-tar com compressão xz nível 1$N$nisto é geralmente muito lento, então$nuse tar não comprimido em vez disso",
		"fz_zip8": "zip com nomes de arquivos utf8 (pode ser instável no windows 7 e mais antigos)",
		"fz_zipd": "zip com nomes de arquivos cp437 tradicionais, para software realmente antigo",
		"fz_zipc": "cp437 com crc32 calculado antecipadamente,$npara MS-DOS PKZIP v2.04g (outubro de 1993)$n(leva mais tempo para processar antes que o download possa começar)",

		"un_m1": "você pode excluir seus uploads recentes (ou abortar os que não foram concluídos) abaixo",
		"un_upd": "atualizar",
		"un_m4": "ou compartilhar os arquivos visíveis abaixo:",
		"un_ulist": "mostrar",
		"un_ucopy": "copiar",
		"un_flt": "filtro opcional:&nbsp; a URL deve conter",
		"un_fclr": "limpar filtro",
		"un_derr": 'a exclusão da despublicação falhou:\n',
		"un_f5": 'algo quebrou, por favor, tente uma atualização ou pressione F5',
		"un_uf5": "desculpe, mas você tem que atualizar a página (por exemplo, pressionando F5 ou CTRL-R) antes que este upload possa ser abortado",
		"un_nou": "<b>aviso:</b> o servidor está muito ocupado para mostrar uploads incompletos; clique no link \"atualizar\" em um momento",
		"un_noc": "<b>aviso:</b> a despublicação de arquivos totalmente enviados não está ativada/permitida na configuração do servidor",
		"un_max": "mostrando os primeiros 2000 arquivos (use o filtro)",
		"un_avail": "{0} uploads recentes podem ser excluídos<br />{1} incompletos podem ser abortados",
		"un_m2": "ordenado por tempo de upload; o mais recente primeiro:",
		"un_no1": "sike! nenhum upload é suficientemente recente",
		"un_no2": "sike! nenhum upload que corresponda a esse filtro é suficientemente recente",
		"un_next": "excluir os próximos {0} arquivos abaixo",
		"un_abrt": "abortar",
		"un_del": "excluir",
		"un_m3": "carregando seus uploads recentes...",
		"un_busy": "excluindo {0} arquivos...",
		"un_clip": "{0} links copiados para a área de transferência",

		"u_https1": "você deveria",
		"u_https2": "mudar para https",
		"u_https3": "para um melhor desempenho",
		"u_ancient": 'seu navegador é impressionantemente antigo -- talvez você devesse <a href="#" onclick="goto(\'bup\')">usar o bup em vez disso</a>',
		"u_nowork": "precisa do firefox 53+ ou chrome 57+ ou iOS 11+",
		"tail_2old": "precisa do firefox 105+ ou chrome 71+ ou iOS 14.5+",
		"u_nodrop": 'seu navegador é muito antigo para upload de arrastar e soltar',
		"u_notdir": "isso não é uma pasta!\n\nseu navegador é muito antigo,\npor favor, tente arrastar e soltar em vez disso",
		"u_uri": "para arrastar e soltar imagens de outras janelas do navegador,\npor favor, solte-as no grande botão de upload",
		"u_enpot": 'mudar para <a href="#">UI batata</a> (pode melhorar a velocidade de upload)',
		"u_depot": 'mudar para <a href="#">UI chique</a> (pode reduzir a velocidade de upload)',
		"u_gotpot": 'mudando para a UI batata para uma velocidade de upload melhorada,\n\nsinta-se à vontade para discordar e voltar!',
		"u_pott": "<p>arquivos: &nbsp; <b>{0}</b> concluídos, &nbsp; <b>{1}</b> falhados, &nbsp; <b>{2}</b> ocupados, &nbsp; <b>{3}</b> na fila</p>",
		"u_ever": "este é o uploader básico; up2k precisa de pelo menos<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'este é o uploader básico; <a href="#" id="u2yea">up2k</a> é melhor',
		"u_uput": 'otimizar para velocidade (pular checksum)',
		"u_ewrite": 'você não tem acesso de escrita a esta pasta',
		"u_eread": 'você não tem acesso de leitura a esta pasta',
		"u_enoi": 'a busca de arquivos não está ativada na configuração do servidor',
		"u_enoow": "substituir não funcionará aqui; precisa de permissão de Excluir",
		"u_badf": 'Estes {0} arquivos (de um total de {1}) foram ignorados, possivelmente devido a permissões do sistema de arquivos:\n\n',
		"u_blankf": 'Estes {0} arquivos (de um total de {1}) estão em branco / vazios; enviá-los de qualquer maneira?\n\n',
		"u_applef": 'Estes {0} arquivos (de um total de {1}) são provavelmente indesejáveis;\nPressione <code>OK/Enter</code> para PULAR os seguintes arquivos,\nPressione <code>Cancelar/ESC</code> para NÃO excluir, e ENVIAR esses também:\n\n',
		"u_just1": '\nTalvez funcione melhor se você selecionar apenas um arquivo',
		"u_ff_many": "se você estiver usando <b>Linux / MacOS / Android,</b> então essa quantidade de arquivos <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>pode</em> travar o Firefox!</a>\nse isso acontecer, por favor, tente novamente (ou use o Chrome).",
		"u_up_life": "Este upload será excluído do servidor\n{0} após ser concluído",
		"u_asku": 'enviar estes {0} arquivos para <code>{1}</code>',
		"u_unpt": "você pode desfazer / excluir este upload usando o 🧯 no canto superior esquerdo",
		"u_bigtab": 'prestes a mostrar {0} arquivos\n\nisto pode travar seu navegador, tem certeza?',
		"u_scan": 'Escaneando arquivos...',
		"u_dirstuck": 'o iterador de diretório travou ao tentar acessar os seguintes {0} itens; irá pular:',
		"u_etadone": 'Concluído ({0}, {1} arquivos)',
		"u_etaprep": '(preparando para enviar)',
		"u_hashdone": 'hash concluído',
		"u_hashing": 'hash',
		"u_hs": 'handshaking...',
		"u_started": "os arquivos estão sendo enviados agora; veja [🚀]",
		"u_dupdefer": "duplicado; será processado após todos os outros arquivos",
		"u_actx": "clique neste texto para evitar perda de<br />desempenho ao mudar para outras janelas/abas",
		"u_fixed": "OK!&nbsp; Consertado 👍",
		"u_cuerr": "falha ao enviar o bloco {0} de {1};\nprovavelmente inofensivo, continuando\n\narquivo: {2}",
		"u_cuerr2": "o servidor rejeitou o upload (bloco {0} de {1});\ntentará novamente mais tarde\n\narquivo: {2}\n\nerro ",
		"u_ehstmp": "tentará novamente; veja no canto inferior direito",
		"u_ehsfin": "o servidor rejeitou a solicitação para finalizar o upload; tentando novamente...",
		"u_ehssrch": "o servidor rejeitou a solicitação para realizar a busca; tentando novamente...",
		"u_ehsinit": "o servidor rejeitou a solicitação para iniciar o upload; tentando novamente...",
		"u_eneths": "erro de rede ao realizar o handshake de upload; tentando novamente...",
		"u_enethd": "erro de rede ao testar a existência do alvo; tentando novamente...",
		"u_cbusy": "esperando o servidor confiar em nós novamente após uma falha de rede...",
		"u_ehsdf": "o servidor ficou sem espaço em disco!\n\ncontinuará tentando novamente, caso alguém\nlibere espaço suficiente para continuar",
		"u_emtleak1": "parece que seu navegador pode ter um vazamento de memória;\npor favor,",
		"u_emtleak2": ' <a href="{0}">mude para https (recomendado)</a> ou ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'tente o seguinte:\n<ul><li>pressione <code>F5</code> para atualizar a página</li><li>depois desative o botão &nbsp;<code>mt</code>&nbsp; nas &nbsp;<code>⚙️ configurações</code></li><li>e tente o upload novamente</li></ul>Os uploads serão um pouco mais lentos, mas tudo bem.\nDesculpe pelo problema !\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">tem uma correção de bug</a> para isso',
		"u_emtleakf": 'tente o seguinte:\n<ul><li>pressione <code>F5</code> para atualizar a página</li><li>depois ative <code>🥔</code> (batata) na UI de upload<li>e tente o upload novamente</li></ul>\nPS: o firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">esperançosamente terá uma correção de bug</a> em algum momento',
		"u_s404": "não encontrado no servidor",
		"u_expl": "explicar",
		"u_maxconn": "a maioria dos navegadores limita isso a 6, mas o firefox permite que você aumente com <code>connections-per-server</code> em <code>about:config</code>",
		"u_tu": '<p class="warn">AVISO: turbo ativado, <span>&nbsp;o cliente pode não detectar e retomar uploads incompletos; veja a dica de ferramenta do botão turbo</span></p>',
		"u_ts": '<p class="warn">AVISO: turbo ativado, <span>&nbsp;os resultados da busca podem estar incorretos; veja a dica de ferramenta do botão turbo</span></p>',
		"u_turbo_c": "o turbo está desativado na configuração do servidor",
		"u_turbo_g": "desativando o turbo porque você não tem\n privilégios de listagem de diretório neste volume",
		"u_life_cfg": 'excluir automaticamente depois de <input id="lifem" p="60" /> min (ou <input id="lifeh" p="3600" /> horas)',
		"u_life_est": 'o upload será excluído <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'esta pasta impõe um\n tempo de vida máximo de {0}',
		"u_unp_ok": 'a despublicação é permitida para {0}',
		"u_unp_ng": 'a despublicação NÃO será permitida',
		"ue_ro": 'seu acesso a esta pasta é Somente Leitura\n\n',
		"ue_nl": 'você não está logado no momento',
		"ue_la": 'você está logado no momento como "{0}"',
		"ue_sr": 'você está no modo de busca de arquivos no momento\n\nmude para o modo de upload clicando na lupa 🔎 (ao lado do grande botão BUSCAR), e tente enviar novamente\n\ndesculpe',
		"ue_ta": 'tente enviar novamente, deve funcionar agora',
		"ue_ab": "este arquivo já está sendo enviado para outra pasta, e esse upload deve ser concluído antes que o arquivo possa ser enviado para outro lugar.\n\nVocê pode abortar e esquecer o upload inicial usando o 🧯 no canto superior esquerdo",
		"ur_1uo": "OK: Arquivo enviado com sucesso",
		"ur_auo": "OK: Todos os {0} arquivos enviados com sucesso",
		"ur_1so": "OK: Arquivo encontrado no servidor",
		"ur_aso": "OK: Todos os {0} arquivos encontrados no servidor",
		"ur_1un": "O upload falhou, desculpe",
		"ur_aun": "Todos os {0} uploads falharam, desculpe",
		"ur_1sn": "O arquivo NÃO foi encontrado no servidor",
		"ur_asn": "Os {0} arquivos NÃO foram encontrados no servidor",
		"ur_um": "Concluído;\n{0} uploads OK,\n{1} uploads falharam, desculpe",
		"ur_sm": "Concluído;\n{0} arquivos encontrados no servidor,\n{1} arquivos NÃO encontrados no servidor",

		"lang_set": "atualizar para a mudança ter efeito?"
	},
	"rus": {
		"tt": "Русский",

		"cols": {
			"c": "кнопки действий",
			"dur": "длительность",
			"q": "качество / битрейт",
			"Ac": "аудио кодек",
			"Vc": "видео кодек",
			"Fmt": "формат / контейнер",
			"Ahash": "контрольная сумма аудио",
			"Vhash": "контрольная сумма видео",
			"Res": "разрешение",
			"T": "тип файла",
			"aq": "качество аудио / битрейт",
			"vq": "качество видео / битрейт",
			"pixfmt": "сабсемплинг / пиксельный формат",
			"resw": "горизонтальное разрешение",
			"resh": "вертикальное разрешение",
			"chs": "аудио каналы",
			"hz": "частота дискретизации"
		},

		"hks": [
			[
				"разное",
				["ESC", "закрыть всякие штуки"],

				"файловый менеджер",
				["G", "переключиться между списком / плиткой"],
				["T", "переключиться между миниатюрами / иконками"],
				["⇧ A/D", "размер миниатюры"],
				["ctrl-K", "удалить выделенное"],
				["ctrl-X", "вырезать выделенное в буфер"],
				["ctrl-C", "копировать выделенное в буфер"],
				["ctrl-V", "вставить (переместить/копировать) сюда"],
				["Y", "скачать выделенное"],
				["F2", "переименовать выделенное"],

				"выделение файлов",
				["пробел", "выделить/снять выделение с текущего файла"],
				["↑/↓", "двигать курсор"],
				["ctrl ↑/↓", "двигать курсор и скроллить"],
				["⇧ ↑/↓", "выделить предыдущий/следующий файл"],
				["ctrl-A", "выделить все файлы и папки"],
			], [
				"навигация",
				["B", "показать/скрыть панель навигации"],
				["I/K", "предыдущая/следующая папка"],
				["M", "перейти на уровень выше (или свернуть текущую папку)"],
				["V", "переключиться между папками / текстовыми файлами в панели навигации"],
				["A/D", "уменьшить/увеличить панель навигации"],
			], [
				"аудиоплеер",
				["J/L", "предыдущий/следующий трек"],
				["U/O", "перемотать на 10 секунд назад/вперёд"],
				["0..9", "перемотать на 0%..90%"],
				["P", "играть/пауза (или подгрузить трек)"],
				["S", "выделить текущий трек"],
				["Y", "скачать трек"],
			], [
				"просмотрщик изображений",
				["J/L, ←/→", "предыдущее/следующее изображение"],
				["Home/End", "первое/последнее изображение"],
				["F", "развернуть на полный экран"],
				["R", "повернуть по часовой стрелке"],
				["⇧ R", "повернуть против часовой стрелки"],
				["S", "выделить изображение"],
				["Y", "скачать изображение"],
			], [
				"видеоплеер",
				["U/O", "перемотать на 10 секунд назад/вперёд"],
				["P/K/Space", "играть/пауза"],
				["C", "продолжить проигрывать следующее"],
				["V", "повтор"],
				["M", "выключить звук"],
				["[ and ]", "задать интервал повтора"],
			], [
				"просмотрщик текстовых файлов",
				["I/K", "предыдущий/следующий файл"],
				["M", "закрыть файл"],
				["E", "отредактировать файл"],
				["S", "выделить файл"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Отмена",

		"enable": "Включить",
		"danger": "ВНИМАНИЕ",
		"clipped": "скопировано в буфер обмена",

		"ht_s1": "секунда",
		"ht_s2": "секунды",
		"ht_m1": "минута",
		"ht_m2": "минуты",
		"ht_h1": "час",
		"ht_h2": "часы",
		"ht_d1": "день",
		"ht_d2": "дни",
		"ht_and": " и ",

		"goh": "панель управления",
		"gop": 'предыдущая папка">пред',
		"gou": 'родительская папка">вверх',
		"gon": 'следующая папка">след',
		"logout": "Выйти ",
		"login": "Войти", //m
		"access": " доступ",
		"ot_close": "закрыть подменю",
		"ot_search": "искать файлы по атрибутам, пути / имени, музыкальным тегам или любой другой комбинации из следующих конструкций$N$N&lt;code&gt;foo bar&lt;/code&gt; = обязано содержать «foo» И «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = обязано содержать «foo», но не «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = начинается с «yana» и имеет расширение «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = содержит именно «try unite»$N$Nформат времени задаётся по стандарту iso-8601, например$N&lt;code&gt;2009-12-31&lt;/code&gt; или &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: удалить ваши недавние загрузки и отменить незавершённые",
		"ot_bup": "bup: легковесный загрузчик файлов, поддерживает даже netscape 4.0",
		"ot_mkdir": "mkdir: создать новую папку",
		"ot_md": "new-md: создать новый markdown-документ",
		"ot_msg": "msg: отправить сообщение в лог сервера",
		"ot_mp": "настройка медиаплеера",
		"ot_cfg": "остальные настройки",
		"ot_u2i": 'up2k: загрузить файлы (если имеется доступ к записи) или переключиться в режим поиска$N$Nзагрузки являются возобновляемыми и многопоточными, а даты изменения файлов сохраняются в процессе, но этот метод использует больше ресурсов процессора, чем [🎈]&nbsp; (легковесный загрузчик)<br /><br />во время загрузки эта иконка превращается в индикатор!',
		"ot_u2w": 'up2k: загрузить файлы с поддержкой возобновления (закиньте те же файлы после перезапуска браузера)$N$Nподдерживается многопоточность, даты изменения файлов сохраняются в процессе, но этот метод использует больше ресурсов процессора, чем [🎈]&nbsp; (легковесный загрузчик)<br /><br />во время загрузки эта иконка превращается в индикатор!',
		"ot_noie": 'Пожалуйста, используйте Chrome / Firefox / Edge',

		"ab_mkdir": "создать папку",
		"ab_mkdoc": "создать markdown-документ",
		"ab_msg": "отправить сообщение в лог сервера",

		"ay_path": "перейти к папкам",
		"ay_files": "перейти к файлам",

		"wt_ren": "переименовать выделенные файлы$NГорячая клавиша: F2",
		"wt_del": "удалить выделенные файлы$NГорячая клавиша: ctrl-K",
		"wt_cut": "вырезать выделенные файлы &lt;small&gt;(затем вставить куда-то в другое место)&lt;/small&gt;$NГорячая клавиша: ctrl-X",
		"wt_cpy": "копировать выделенные файлы в буфер$N(чтобы вставить их куда-то ещё)$NГорячая клавиша: ctrl-C",
		"wt_pst": "вставить ранее вырезанный / скопированный файл$NГорячая клавиша: ctrl-V",
		"wt_selall": "выделить все файлы$NГорячая клавиша: ctrl-A (когда выделен хотя бы один файл)",
		"wt_selinv": "инвертировать выделение",
		"wt_zip1": "скачать эту папку как архив",
		"wt_selzip": "скачать выделенные файлы как архив",
		"wt_seldl": "скачать выделенные файлы по-отдельности$NГорячая клавиша: Y",
		"wt_npirc": "копировать информацию о треке в формате irc",
		"wt_nptxt": "копировать информацию о треке обычным текстом",
		"wt_m3ua": "добавить в плейлист m3u (нажмите <code>📻коп.</code> в конце)",
		"wt_m3uc": "копировать плейлист m3u в буфер обмена",
		"wt_grid": "переключить между сеткой / списком$NГорячая клавиша: G",
		"wt_prev": "предыдущий трек$NГорячая клавиша: J",
		"wt_play": "играть / пауза$NГорячая клавиша: P",
		"wt_next": "следующий трек$NГорячая клавиша: L",

		"ul_par": "параллельные загрузки:",
		"ut_rand": "случайные имена файлов",
		"ut_u2ts": "копировать время последнего изменения$Nиз вашей файловой системы на сервер\">📅",
		"ut_ow": "перезаписывать существующие файлы на сервере?$N🛡️: нет (для повторяющихся файлов будут создаваться новые имена)$N🕒: перезаписать файлы с датой изменения старее, чем у загружаемых$N♻️: всегда перезаписывать (если файлы различаются по содержанию)",
		"ut_mt": "продолжать хешировать другие файлы во время загрузки$N$Nесть смысл отключить при медленном диске или процессоре",
		"ut_ask": 'требовать подтверждения перед началом загрузки">💭',
		"ut_pot": "улучшить скорость загрузки на слабых устройства$Nс помощью упрощения интерфейса",
		"ut_srch": "не загружать, а проверять, существуют ли данные файлы $N на сервере (проверка всех доступных вам папок)",
		"ut_par": "при 0 загрузка встанет на паузу$N$Nследует повысить, если ваше подключение медленное$N$Nоставьте 1, если используется локальная сеть или диск сервера медленный",
		"ul_btn": "отпустите файлы / папки<br>здесь (или нажмите)",
		"ul_btnu": "З А Г Р У З И Т Ь",
		"ul_btns": "И С К А Т Ь",

		"ul_hash": "хеш",
		"ul_send": "отправка",
		"ul_done": "готово",
		"ul_idle1": "нет загрузок в очереди",
		"ut_etah": "средняя скорость &lt;em&gt;хеширования&lt;/em&gt; и примерное время до завершения",
		"ut_etau": "средняя скорость &lt;em&gt;загрузки&lt;/em&gt; и примерное время до завершения",
		"ut_etat": "средняя &lt;em&gt;общая&lt;/em&gt; скорость и примерное время до завершения",

		"uct_ok": "успешно завершены",
		"uct_ng": "ошибки / отказы / не найдены",
		"uct_done": "готово (ok и ng вместе)",
		"uct_bz": "хешируются или загружаются",
		"uct_q": "в очереди",

		"utl_name": "имя файла",
		"utl_ulist": "список",
		"utl_ucopy": "копировать",
		"utl_links": "ссылки",
		"utl_stat": "статус",
		"utl_prog": "прогресс",

		// keep short:
		"utl_404": "404",
		"utl_err": "ОШИБКА",
		"utl_oserr": "ошибка ОС",
		"utl_found": "найдено",
		"utl_defer": "отложить",
		"utl_yolo": "турбо",
		"utl_done": "готово",

		"ul_flagblk": "файлы были добавлены в очередь</b>,<br>однако в другой вкладке уже есть активная загрузка через up2k,<br>поэтому ожидаем её завершения",
		"ul_btnlk": "настройки сервера запрещают изменение состояния этой опции",

		"udt_up": "Загрузить",
		"udt_srch": "Поиск",
		"udt_drop": "отпустите здесь",

		"u_nav_m": '<h6>лады, что там у вас?</h6><code>Enter</code> = Файлы (один или больше)\n<code>ESC</code> = Одна папка (с учётом подпапок)',
		"u_nav_b": '<a href="#" id="modal-ok">Файлы</a><a href="#" id="modal-ng">Одна папка</a>',

		"cl_opts": "переключатели",
		"cl_themes": "тема",
		"cl_langs": "язык",
		"cl_ziptype": "архивация папок",
		"cl_uopts": "опции up2k",
		"cl_favico": "иконка",
		"cl_bigdir": "бол. папки",
		"cl_hsort": "#сорт.",
		"cl_keytype": "схема горячих клавиш",
		"cl_hiddenc": "скрытые столбцы",
		"cl_hidec": "скрыть",
		"cl_reset": "сбросить",
		"cl_hpick": "нажмите на заголовки столбцов, чтобы скрыть их в таблице ниже",
		"cl_hcancel": "скрытие столбца отменено",

		"ct_grid": '田 сетка',
		"ct_ttips": '◔ ◡ ◔">ℹ️ подсказки',
		"ct_thumb": 'переключение между иконками и миниатюрами в режиме сетки$NГорячая клавиша: T">🖼️ миниат.',
		"ct_csel": 'держите CTRL или SHIFT для выделения файлов в режиме сетки">выбор',
		"ct_ihop": 'показывать последний открытый файл после закрытия просмотрщика изображений">g⮯',
		"ct_dots": 'показывать скрытые файлы (если есть доступ)">скрыт.',
		"ct_qdel": 'спрашивать подтверждение только один раз перед удалением файлов">быстр. удал.',
		"ct_dir1st": 'разместить папки над файлами">📁 сверху',
		"ct_nsort": 'сортировка по числам$N(например, файл с &gt;code&lt;2&gt;/code&lt; в начале названия идёт перед &gt;code&lt;11&gt;/code&lt;)">нат. сорт.',
		"ct_utc": 'используйте UTC для всех временных меток">UTC', //m
		"ct_readme": 'показывать содержимое README.md в описании папки">📜 ридми',
		"ct_idxh": 'показывать страницу index.html в текущей папке вместо интерфейса">htm',
		"ct_sbars": 'показывать полосы прокрутки">⟊',

		"cut_umod": "если файл уже существует на сервере, обновить время последнего изменения на сервере в соответствии с локальным файлом (требуются права write+delete)\">перенос 📅",

		"cut_turbo": "используйте эту функцию С ОСТОРОЖНОСТЬЮ:$N$Nпригодится в случае, если была прервана загрузка большого количества файлов, и вы хотите возобновить её как можно быстрее$N$Nпроверка файлов по хешу заменяется на простой алгоритм: <em>&quot;если размер файла отличается - тогда загрузить&quot;</em>, но содержание файлов не сравнивается$N$Nследует отключить эту функцию после окончания загрузки, а затем &quot;загрузить&quot; те же файлы заново, чтобы валидировать их\">турбо",

		"cut_datechk": "работает только при включённой кнопке &quot;турбо&quot;$N$Nчуть-чуть повышает надёжность турбо-загрузок с помощью сверки дат изменений между файлами на сервере и вашими$N$N<em>в теории</em> достаточно для проверки большинства незавершённых / повреждённых загрузок, но не является альтернативой валидации файлов после турбо-загрузки\">провер. дат",

		"cut_u2sz": "размер (в МиБ) каждой загружаемой части; большие значения показывают лучшие результаты для дальних соединений. Если подключение нестабильное, попробуйте значение пониже",

		"cut_flag": "разрешить одновременную загрузку только из одной вкладки за раз $N -- обязательно включить эту опцию в остальных вкладках $N -- работает только в пределах одного домена",

		"cut_az": "загружать файлы в алфавитном порядке вместо &quot;от меньшего к большему&quot;$N$Nэто позволит проще отследить проблемы во время загрузки, но скорость слегка ниже на очень быстрых соединениях (например, в локальной сети)",

		"cut_nag": "системное уведомление по завершении загрузки$N(только при неактивной вкладке браузера)",
		"cut_sfx": "звуковое уведомление по завершении загрузки$N(только при неактивной вкладке браузера)",

		"cut_mt": "использовать многопоточность для ускорения хеширования$N$Nиспользует Web Worker'ы и требует больше памяти (до 512 МиБ)$N$Nускоряет https на 30%, http - в 4,5 раз\">мп",

		"cut_wasm": "использовать модуль WASM вместо встроенной в браузер функции хеширования; ускоряет процесс в браузерах на основе Chromium, но увеличивает нагрузку на процессор. Старые версии Chrome содержат баги, которые заполняют всю оперативную память и крашат браузер, когда включена эта опция\">wasm",

		"cft_text": "текст для иконки (очистите поле и перезагрузите страницу для применения)",
		"cft_fg": "цвет текста",
		"cft_bg": "цвет фона",

		"cdt_lim": "максимальное количество файлов для показа в папке",
		"cdt_ask": "внизу страницы спрашивать о действии вместо автоматической загрузки следующих файлов",
		"cdt_hsort": "сколько правил сортировки (&lt;code&gt;,sorthref&lt;/code&gt;) включать в адрес страницы. Если значение равно 0, по нажатии на ссылки будут игнорироваться правила, включённые в них",

		"tt_entree": "показать панель навигации$NГорячая клавиша: B",
		"tt_detree": "скрыть панель навигации$NГорячая клавиша: B",
		"tt_visdir": "прокрутить до выделенной папки",
		"tt_ftree": "переключить между иерархией и списком текстовых файлов$NГорячая клавиша: V",
		"tt_pdock": "закрепить родительские папки сверху панели",
		"tt_dynt": "автоматическое расширение панели",
		"tt_wrap": "перенос слов",
		"tt_hover": "раскрывать обрезанные строки при наведении$N( ломает скроллинг, если $N&nbsp; курсор не в пустоте слева )",

		"ml_pmode": "в конце папки...",
		"ml_btns": "команды",
		"ml_tcode": "транскодировать",
		"ml_tcode2": "транскод. в",
		"ml_tint": "затемн.",
		"ml_eq": "эквалайзер",
		"ml_drc": "компрессор",

		"mt_loop": "повторять один трек\">🔁",
		"mt_one": "остановить после этого трека\">1️⃣",
		"mt_shuf": "перемешать треки во всех папках\">🔀",
		"mt_aplay": "автоматически играть треки по нажатии на ссылки с их ID$N$Nпри отключении адрес сайта также перестанет обновляться в соответствии с текущим треком\">a▶",
		"mt_preload": "подгружать следующий трек перед концом текущего для бесшовного переключения\">предзагр.",
		"mt_prescan": "переходить в следующую папку перед окончанием последнего трека$Nне даёт браузеру прервать следующий плейлист\">нав.",
		"mt_fullpre": "подгружать следующий трек целиком;$N✅ полезно при <b>нестабильном</b> подключении,$N❌ при медленной скорости лучше <b>выключить</b>\">цел.",
		"mt_fau": "для телефонов: начинать следующий трек сразу, даже если он не успел подгрузиться целиком (может сломать отображение тегов)\">☕️",
		"mt_waves": "визуализация:$Nпоказывать волну громкости на полосе воспроизведения\">~",
		"mt_npclip": "показать кнопки копирования для текущего трека\">/np",
		"mt_m3u_c": "показать кнопки копирования для выделенных треков$Nв формате плейлистов m3u8\">📻",
		"mt_octl": "интеграция с ОС (поддержка медиа-клавиш и музыкальных виджетов)\">интегр.",
		"mt_oseek": "позволить перематывать треки через системные виджеты$N$Nвнимание: на некоторых устройствах (iPhone)$Nэто заменит кнопку следующего трека\">перемотка",
		"mt_oscv": "показывать картинки альбомов в виджетах\">арт",
		"mt_follow": "держать фокус на играющем треке\">🎯",
		"mt_compact": "компактный плеер\">⟎",
		"mt_uncache": "очистить кеш &nbsp;(если браузер кешировал повреждённый$Nтрек и отказывается его запускать)\">уд. кеш",
		"mt_mloop": "повторять треки в папке\">🔁 цикл",
		"mt_mnext": "загрузить следующую папку и продолжить в ней\">📂 след.",
		"mt_mstop": "приостановить воспроизведение\">⏸ стоп",
		"mt_cflac": "конвертировать flac / wav в {0}\">flac",
		"mt_caac": "конвертировать aac / m4a в {0}\">aac",
		"mt_coth": "конвертировать всё остальное (кроме mp3) в {0}\">др.",
		"mt_c2opus": "лучший вариант для компьютеров и устройств на Android\">opus",
		"mt_c2owa": "opus-weba, для iOS 17.5 и выше\">owa",
		"mt_c2caf": "opus-caf, для iOS 11-17\">caf",
		"mt_c2mp3": "для очень старых устройств\">mp3",
		"mt_c2flac": "лучшее качество звука, но большие файлы\">flac", //m
		"mt_c2wav": "не сжатое воспроизведение (ещё больше)\">wav", //m
		"mt_c2ok": "хороший выбор",
		"mt_c2nd": "это не рекомендованный вариант формата для вашего устройства, но сойдёт",
		"mt_c2ng": "не похоже, что ваше устройство поддерживает этот формат, но давайте попробуем и узнаем наверняка",
		"mt_xowa": "в iOS есть баги, препятствующие фоновому воспроизведению этого формата. Пожалуйста, используйте caf или mp3",
		"mt_tint": "непрозрачность фона (0-100) на полосе воспроизведения$N$Nделает буферизацию менее отвлекающей",
		"mt_eq": "включить эквалайзер$N$Nboost &lt;code&gt;0&lt;/code&gt; = стандартная громкость$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = обычное стерео$Nwidth &lt;code&gt;0.5&lt;/code&gt; = микширование левого и правого каналов на 50%$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = моно$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; и width &lt;code&gt;10&lt;/code&gt; = удаление голоса :^)$N$Nвключённый эквалайзер полностью убирает задержку между треками, поэтому следует его включить со всеми значениями на 0 (кроме width = 1), если вам нужно бесшовное воспроизведение",
		"mt_drc": "включить компрессор; также включит эквалайзер для баланса вселенной, так что выставьте всё на 0 кроме width, если он вам не нужен$N$Nпонижает громкость при волне выше значения dB в tresh; каждый dB в ratio равен одному dB на выходе, так что стандартные значения tresh = -24 и ratio = 12 сделают так, что звук никогда не будет громче -22 dB. При таком раскладе можно поставить boost в эквалайзере на 0.8 или даже 1.8 при значении atk = 0 и огромном rls вроде 90 (работает только в Firefox, rls не может быть выше 1 в других браузерах)$N$N(загляните в википедию, там всё объяснено подробнее)",

		"mb_play": "играть",
		"mm_hashplay": "воспроизвести этот музыкальный файл?",
		"mm_m3u": "нажмите <code>Enter/OK</code>, чтобы играть\nнажмите <code>ESC/Отмена</code>, чтобы редактировать",
		"mp_breq": "требуется Firefox 82+, Chrome 73+ или iOS 15+",
		"mm_bload": "загружаю...",
		"mm_bconv": "конвертирую в {0}, подождите...",
		"mm_opusen": "ваш браузер не может воспроизводить файлы aac / m4a;\nвключено транскодирование в opus",
		"mm_playerr": "ошибка воспроизведения: ",
		"mm_eabrt": "Попытка воспроизведения была отменена",
		"mm_enet": "Ваше подключение нестабильно",
		"mm_edec": "Этот файл, возможно, повреждён??",
		"mm_esupp": "Ваш браузер не распознаёт этот аудио-формат",
		"mm_eunk": "Неопознанная ошибка",
		"mm_e404": "Не удалось воспроизвести аудио; ошибка 404: Файл не найден.",
		"mm_e403": "Не удалось воспроизвести аудио; ошибка 403: Доступ запрещён.\n\nПопробуйте перезагрузить страницу, возможно, ваша сессия истекла",
		"mm_e500": "Не удалось воспроизвести аудио; ошибка 500: Проверьте логи сервера.",
		"mm_e5xx": "Не удалось воспроизвести аудио; ошибка сервера ",
		"mm_nof": "больше аудио-файлов не найдено",
		"mm_prescan": "Поиск музыки для воспроизведения дальше...",
		"mm_scank": "Найден следующий трек:",
		"mm_uncache": "кеш очищен; все треки будут загружены заново при воспроизведении",
		"mm_hnf": "это трек больше не существует",

		"im_hnf": "это изображение больше не существует",

		"f_empty": 'эта папка пуста',
		"f_chide": 'это скроет столбец «{0}»\n\nвы можете показать скрытые столбцы в настройках',
		"f_bigtxt": "объём данного файла - {0} МиБ. точно открыть как текст?",
		"f_bigtxt2": "просмотреть только конец файла? это также включит обновление в реальном времени, показывая новые строки сразу после их добавления",
		"fbd_more": '<div id="blazy">показано <code>{0}</code> из <code>{1}</code> файлов; <a href="#" id="bd_more">показать {2}</a> или <a href="#" id="bd_all">показать всё</a></div>',
		"fbd_all": '<div id="blazy">показано <code>{0}</code> из <code>{1}</code> файлов; <a href="#" id="bd_all">показать всё</a></div>',
		"f_anota": "только {0} из {1} файлов было выделено;\nчтобы выделить всё папку, отмотайте до низа",

		"f_dls": 'ссылки на файлы в данной папке были\nзаменены ссылками на скачивание',

		"f_partial": "Чтобы безопасно скачать файл, который в текущий момент загружается, нажмите на файл с таким же названием, но без расширения <code>.PARTIAL</code>. Пожалуйста, нажмите Отмена или ESC, чтобы сделать это.\n\nПри нажатии OK / Enter, вы скачаете этот временный файл, который с огромной вероятностью содержит лишь неполные данные.",

		"ft_paste": "вставить {0} файлов$NГорячая клавиша: ctrl-V",
		"fr_eperm": 'не удалось переименовать:\nу вас нет разрешения “move” в этой папке',
		"fd_eperm": 'не удалось удалить:\nу вас нет разрешения “delete” в этой папке',
		"fc_eperm": 'не удалось вырезать:\nу вас нет разрешения “move” в этой папке',
		"fp_eperm": 'не удалось вставить:\nу вас нет разрешения “write” в этой папке',
		"fr_emore": "выделите хотя бы один файл, чтобы переименовать",
		"fd_emore": "выделите хотя бы один файл, чтобы удалить",
		"fc_emore": "выделите хотя бы один файл, чтобы вырезать",
		"fcp_emore": "выделите хотя бы один файл, чтобы скопировать в буфер",

		"fs_sc": "поделиться текущей папкой",
		"fs_ss": "поделиться выделенными файлами",
		"fs_just1d": "вы не можете выбрать больше одной папки\nили смешивать файлы с папками при выделении",
		"fs_abrt": "❌ отменить",
		"fs_rand": "🎲 случ. имя",
		"fs_go": "✅ создать доступ",
		"fs_name": "имя",
		"fs_src": "путь",
		"fs_pwd": "пароль",
		"fs_exp": "срок",
		"fs_tmin": "мин",
		"fs_thrs": "часов",
		"fs_tdays": "дней",
		"fs_never": "вечно",
		"fs_pname": "имя ссылки; генерируется случайно если не указано",
		"fs_tsrc": "путь к файлу или папке, которыми нужно поделиться",
		"fs_ppwd": "пароль (необязательно)",
		"fs_w8": "создаю доступ...",
		"fs_ok": "нажмите <code>Enter/OK</code>, чтобы скопировать\nнажмите <code>ESC/Отмена</code>, чтобы закрыть",

		"frt_dec": "может исправить некоторые случаи с некорректными именами файлов\">декодировать url",
		"frt_rst": "сбросить изменённые имена обратно к оригинальным\">↺ сброс",
		"frt_abrt": "отменить операцию и закрыть это окно\">❌ отмена",
		"frb_apply": "ПЕРЕИМЕНОВАТЬ",
		"fr_adv": "переименование массовое / метаданных / по шаблону\">эксперт",
		"fr_case": "чувствительный к регистру regex\">РеГиСтР",
		"fr_win": "совместимые с windows имена; заменяет <code>&lt;&gt;:&quot;\\|?*</code> японскими полноширинными символами\">win",
		"fr_slash": "заменяет <code>/</code> символом, который не создаёт новые папки\">без /",
		"fr_re": "поиск по шаблону regex, применяемый к оригинальным именам; группы захвата могут применяться в поле форматирования с помощью &lt;code&gt;(1)&lt;/code&gt; и &lt;code&gt;(2)&lt;/code&gt; и так далее",
		"fr_fmt": "вдохновлено foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; заменяется названием трека,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; пропускает [эту] часть, если композитор не указан$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; добавляет ведущие нули до двух цифр",
		"fr_pdel": "удалить",
		"fr_pnew": "сохранить как",
		"fr_pname": "предоставьте название для нового шаблона",
		"fr_aborted": "прервано",
		"fr_lold": "старое имя",
		"fr_lnew": "новое имя",
		"fr_tags": "теги для выделенных файлов (не редактируется, это для инструкции):",
		"fr_busy": "переименовываю {0} файлов...\n\n{1}",
		"fr_efail": "ошибка переименования:\n",
		"fr_nchg": "{0} новых имён были модифицированы для соответствия опциям <code>win</code> и/или <code>без /</code>\n\nХотите использовать эти имена?",

		"fd_ok": "успешно удалено",
		"fd_err": "ошибка удаления:\n",
		"fd_none": "ничего не удалено; возможно, не позволяет конфигурация сервера (xbd)?",
		"fd_busy": "удалено {0} файлов...\n\n{1}",
		"fd_warn1": "УДАЛИТЬ эти {0} файлов?",
		"fd_warn2": "<b>Внимание!</b> Это необратимый процесс. Удалить?",

		"fc_ok": "вырезано {0} файлов",
		"fc_warn": 'вырезано {0} файлов\n\nно только <b>эта</b> вкладка браузера может их вставить\n(поскольку выделение оказалось настолько огромным)',

		"fcc_ok": "скопировано {0} файлов в буфер",
		"fcc_warn": 'скопировано {0} файлов в буфер\n\nно только <b>эта</b> вкладка браузера может их вставить\n(поскольку выделение оказалось настолько огромным)',

		"fp_apply": "использовать эти имена",
		"fp_ecut": "сначала вырезать или скопировать только некоторые файлы / папки\n\nучтите: вы можете вырезать / вставлять файлы между вкладками",
		"fp_ename": "{0} файлов невозможно перенести сюда, потому что их имена уже заняты. Введите имена ниже, чтобы продолжить, или оставьте поля пустыми, чтобы пропустить:",
		"fcp_ename": "{0} файлов невозможно скопировать сюда, потому что их имена уже заняты. Введите имена ниже, чтобы продолжить, или оставьте поля пустыми, чтобы пропустить:",
		"fp_emore": "есть ещё коллизии имён, которые требуется исправить",
		"fp_ok": "успешно перенесено",
		"fcp_ok": "успешно скопировано",
		"fp_busy": "перемещаю {0} файлов...\n\n{1}",
		"fcp_busy": "копирую {0} файлов...\n\n{1}",
		"fp_abrt": "прерывание...", //m
		"fp_err": "ошибка перемещения:\n",
		"fcp_err": "ошибка копирования:\n",
		"fp_confirm": "переместить эти {0} файлов сюда?",
		"fcp_confirm": "скопировать эти {0} файлов сюда?",
		"fp_etab": 'ошибка чтения буфера обмена из другой вкладки браузера',
		"fp_name": "загружаю файл с вашего устройства. Назовите его:",
		"fp_both_m": '<h6>выберите, что вставить</h6><code>Enter</code> = Перенести {0} файлов из «{1}»\n<code>ESC</code> = Загрузить {2} файлов с вашего устройства',
		"fcp_both_m": '<h6>выберите, что вставить</h6><code>Enter</code> = Скопировать {0} файлов из «{1}»\n<code>ESC</code> = Загрузить {2} файлов с вашего устройства',
		"fp_both_b": '<a href="#" id="modal-ok">Переместить</a><a href="#" id="modal-ng">Загрузить</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Скопировать</a><a href="#" id="modal-ng">Загрузить</a>',

		"mk_noname": "введите имя в текстовое поле слева перед тем, как это делать :p",

		"tv_load": "Загружаю текстовый документ:\n\n{0}\n\n{1}% ({2} из {3} МиБ загружено)",
		"tv_xe1": "не удалось загрузить текстовый файл:\n\nошибка ",
		"tv_xe2": "404, файл не найден",
		"tv_lst": "список текстовых файлов в",
		"tvt_close": "вернуться в обзор папки$NГорячая клавиша: M (или Esc)\">❌ закрыть",
		"tvt_dl": "скачать этот файл$NГорячая клавиша: Y\">💾 скачать",
		"tvt_prev": "показать предыдущий документ$NГорячая клавиша: i\">⬆ пред",
		"tvt_next": "показать следующий документ$NГорячая клавиша: K\">⬇ след",
		"tvt_sel": "выбрать документ &nbsp; ( для вырезания / копирования / удаления / ... )$NГорячая клавиша: S\">выд",
		"tvt_edit": "открыть документ в текстовом редакторе$NГорячая клавиша: E\">✏️ изменить",
		"tvt_tail": "проверять файл на изменения; показывать новые строки в реальном времени\">📡 обновлять",
		"tvt_wrap": "перенос слов\">↵",
		"tvt_atail": "прикрепить вид к низу страницы\">⚓",
		"tvt_ctail": "декодировать цвета терминала (ansi escape codes)\">🌈",
		"tvt_ntail": "лимит прокрутки (как много байт текста держать в памяти)",

		"m3u_add1": "трек добавлен в плейлист m3u",
		"m3u_addn": "{0} треков добавлено в плейлист m3u",
		"m3u_clip": "плейлист m3u скопирован в буфер\n\nсоздайте файл с расширением <code>.m3u</code> и вставьте текст туда, чтобы сделать из него плейлист",

		"gt_vau": "не показывать видео, только воспроизводить аудио\">🎧",
		"gt_msel": "включить режим выделения; держите ctrl при нажатии для инвертации действия$N$N&lt;em&gt;когда активно: дважды кликните на файле / папке, чтобы открыть их&lt;/em&gt;$N$NГорячая клавиша: S\">выделение",
		"gt_crop": "обрезать миниатюры\">обрезка",
		"gt_3x": "миниатюры высокого разрешения\">3x",
		"gt_zoom": "размер",
		"gt_chop": "длина имён",
		"gt_sort": "сортировать по",
		"gt_name": "имени",
		"gt_sz": "размеру",
		"gt_ts": "дате",
		"gt_ext": "типу",
		"gt_c1": "укоротить названия файлов",
		"gt_c2": "удлинить названия файлов",

		"sm_w8": "ищем...",
		"sm_prev": "результаты поиска ниже - из предыдущего запроса:\n  ",
		"sl_close": "закрыть результаты поиска",
		"sl_hits": "показ {0} совпадений",
		"sl_moar": "загрузить больше",

		"s_sz": "размер",
		"s_dt": "дата",
		"s_rd": "путь",
		"s_fn": "имя",
		"s_ta": "теги",
		"s_ua": "дата⬆️",
		"s_ad": "другое",
		"s_s1": "минимум МиБ",
		"s_s2": "максимум МиБ",
		"s_d1": "мин. iso8601",
		"s_d2": "макс. iso8601",
		"s_u1": "загружено после",
		"s_u2": "и/или до",
		"s_r1": "путь содержит &nbsp; (разделить пробелами)",
		"s_f1": "имя содержит &nbsp; (для исключения писать -nope)",
		"s_t1": "теги содержат &nbsp; (^=начало, конец=$)",
		"s_a1": "свойства метаданных",

		"md_eshow": "не удалось показать ",
		"md_off": "[📜<em>ридми</em>] отключён в [⚙️] -- документ скрыт",

		"badreply": "Ошибка обработки ответа сервера",

		"xhr403": "403: Доступ запрещён\n\nпопробуйте перезагрузить страницу, возможно, ваша сессия истекла",
		"xhr0": "неизвестно (возможно, потеряно соединение с сервером, либо он отключён)",
		"cf_ok": "просим прощения -- сработала защита от DD" + wah + "oS\n\nвсё должно вернуться в норму через 30 сек\n\nесли ничего не происходит - перезагрузите страницу",
		"tl_xe1": "не удалось показать подпапки:\n\nошибка ",
		"tl_xe2": "404: Папка не найдена",
		"fl_xe1": "не удалось показать файлы:\n\nошибка ",
		"fl_xe2": "404: Папка не найдена",
		"fd_xe1": "не удалось создать подпапку:\n\nошибка ",
		"fd_xe2": "404: Родительская папка не найдена",
		"fsm_xe1": "не удалось отправить сообщение:\n\nошибка ",
		"fsm_xe2": "404: Родительская папка не найдена",
		"fu_xe1": "не удалось удалить список с сервера:\n\nошибка ",
		"fu_xe2": "404: Файл не найден??",

		"fz_tar": "несжатый файл gnu-tar (linux / mac)",
		"fz_pax": "несжатый pax-форматированный tar (медленнее)",
		"fz_targz": "gnu-tar с 3 уровнем сжатия gzip$N$Nобычно это очень медленно,$Nлучше использовать несжатый tar",
		"fz_tarxz": "gnu-tar с 1 уровнем сжатия xz$N$Nобычно это очень медленно,$Nлучше использовать несжатый tar",
		"fz_zip8": "zip с именами по utf8 (может работать криво на windows 7 и ниже)",
		"fz_zipd": "zip с именами по cp437, для очень старого софта",
		"fz_zipc": "cp437 с предварительным вычислением crc32,$N для MS-DOS PKZIP v2.04g (октябрь 1993)$N(требует больше времени для обработки перед скачиванием)",

		"un_m1": "вы можете удалить ваши недавние загрузки (или отменить незавершённые) ниже",
		"un_upd": "обновить",
		"un_m4": "или поделиться файлами снизу:",
		"un_ulist": "показать",
		"un_ucopy": "копировать",
		"un_flt": "опциональный фильтр:&nbsp; адрес должен содержать",
		"un_fclr": "очистить фильтр",
		"un_derr": 'ошибка удаления:\n',
		"un_f5": 'что-то сломалось, пожалуйста перезагрузите страницу',
		"un_uf5": "извините, но вам нужно перезагрузить страницу (F5 или Ctrl+R) перед тем, как отменить эту загрузку",
		"un_nou": '<b>внимание:</b> сервер слишком нагружен, чтобы показать незавершённые загрузки; нажмите на ссылку "обновления" через пару секунд',
		"un_noc": '<b>внимание:</b> удаление уже загруженных файлов запрещено конфигурацией сервера',
		"un_max": "показаны первые 2000 файлов (используйте фильтр)",
		"un_avail": "{0} недавних загрузок может быть удалено<br />{1} незавершённых может быть отменено",
		"un_m2": "отсортировано по времени загрузки; сначала самые последние:",
		"un_no1": "ха, поверил! достаточно свежих загрузок ещё нет",
		"un_no2": "ха, поверил! достаточно свежих загрузок, соответствующих фильтру, ещё нет",
		"un_next": "удалить следующие {0} файлов ниже",
		"un_abrt": "отменить",
		"un_del": "удалить",
		"un_m3": "загружаю ваши недавние загрузки...",
		"un_busy": "удаляю {0} файлов...",
		"un_clip": "{0} ссылок скопировано в буфер",

		"u_https1": "вам стоит",
		"u_https2": "включить https",
		"u_https3": "для лучшей производительности",
		"u_ancient": 'у вас действительно антикварный браузер -- возможно, стоит <a href="#" onclick="goto(\'bup\')">использовать bup</a>',
		"u_nowork": "требуется firefox 53+, chrome 57+ или iOS 11+",
		"tail_2old": "требуется firefox 105+, chrome 71+ или iOS 14.5+",
		"u_nodrop": 'ваш браузер слишком старый для загрузки через перетаскивание',
		"u_notdir": "это не папка!\n\nваш браузер слишком старый,\nиспользуйте перетаскивание",
		"u_uri": "чтобы перетащить картинку из других окон браузера,\nотпустите её на большую кнопку загрузки",
		"u_enpot": 'переключиться на <a href="#">простой интерфейс</a> (может ускорить загрузку)',
		"u_depot": 'переключиться на <a href="#">модный интерфейс</a> (может замедлить загрузку)',
		"u_gotpot": 'переключаюсь на простой интерфес для ускорения загрузки,\n\nможете переключиться обратно, если хотите!',
		"u_pott": "<p>файлы: &nbsp; <b>{0}</b> завершено, &nbsp; <b>{1}</b> ошибок, &nbsp; <b>{2}</b> загружаются, &nbsp; <b>{3}</b> в очереди</p>",
		"u_ever": "это упрощённый загрузчик; up2k требует хотя бы<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'это упрощённый загрузчик; <a href="#" id="u2yea">up2k</a> лучше',
		"u_uput": 'увеличить скорость (пропуск подсчёта контрольных сумм)',
		"u_ewrite": 'у вас нет прав на запись в эту папку',
		"u_eread": 'у вас нет прав на чтение из этой папки',
		"u_enoi": 'поиск файлов выключен настройками сервера',
		"u_enoow": "перезапись здесь не работает; требуются права на удаление",
		"u_badf": 'Эти {0} из {1} файлов были пропущены, вероятно, из-за настроек доступа в файловой системе:\n\n',
		"u_blankf": 'Эти {0} из {1} файлов пустые; всё равно загрузить?\n\n',
		"u_applef": 'Эти {0} из {1} файлов, вероятно, нежелательны;\nНажмите <code>OK/Enter</code>, чтобы ПРОПУСТИТЬ их,\nНажмите <code>Отмена/ESC</code>, чтобы проигнорировать сообщение и ЗАГРУЗИТЬ их:\n\n',
		"u_just1": '\nВозможно, будет лучше, если вы выберете только один файл',
		"u_ff_many": "если вы используете <b>Linux / MacOS / Android,</b> тогда такое количество файлов <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>может</em> крашнуть Firefox!</a>\nв таком случае попробуйте снова (или используйте Chrome).",
		"u_up_life": "Эта загрузка будет удалена с сервера\nчерез {0} после её завершения",
		"u_asku": 'загрузить эти {0} файлов в <code>{1}</code>',
		"u_unpt": "вы можете отменить / удалить эту загрузку с помощью 🧯 сверху слева",
		"u_bigtab": 'будет показано {0} файлов\n\nэто может крашнуть браузер, вы уверены?',
		"u_scan": 'Сканирую файлы...',
		"u_dirstuck": 'сканер папки завис при попытке получить доступ к следующим {0} файлам; будет пропущено:',
		"u_etadone": 'Готово ({0}, {1} файлов)',
		"u_etaprep": '(подготавливаю загрузку)',
		"u_hashdone": 'хеширование выполнено',
		"u_hashing": 'хеш',
		"u_hs": 'подготовка к хешированию...',
		"u_started": "файлы загружаются; подробнее в [🚀]",
		"u_dupdefer": "дубликат; будет обработан после всех остальных файлов",
		"u_actx": "нажмите на этот текст, чтобы предотвратить<br />падение производительности при просмотре других вкладок / окон",
		"u_fixed": "Окей!&nbsp; Исправлено 👍",
		"u_cuerr": "не удалось загрузить фрагмент {0} из {1};\nвероятно, не критично - продолжаю\n\nфайл: {2}",
		"u_cuerr2": "отказ в загрузке (фрагмент {0} из {1});\nпопытаюсь повторить позже\n\nфайл: {2}\n\nошибка ",
		"u_ehstmp": "попытаюсь повторить позже; подробнее снизу справа",
		"u_ehsfin": "отказ в запросе завершения загрузки; повторяю...",
		"u_ehssrch": "отказ в запросе поиска; повторяю...",
		"u_ehsinit": "отказ в запросе начала загрузки; повторяю...",
		"u_eneths": "ошибка подключения во время подготовки загрузки; повторяю...",
		"u_enethd": "ошибка подключения во время проверки существования целевого файла; повторяю...",
		"u_cbusy": "ожидаю возвращения доступа к серверу после ошибки подключения...",
		"u_ehsdf": "на сервере закончилось место!\n\nбуду пытаться повторить, на случай если\nместо будет освобождено",
		"u_emtleak1": "кажется, у вашего браузера может быть утечка памяти;\nпожалуйста,",
		"u_emtleak2": ' <a href="{0}">перейдите на https (рекомендовано)</a> или ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'попробуйте сделать так:\n<ul><li>нажмите <code>F5</code> для обновления страницы</li><li>затем отключите опцию &nbsp;<code>мп</code>&nbsp; в &nbsp;<code>⚙️ настройках</code></li><li>и повторите попытку загрузки</li></ul>Она будет чуть медленнее, но что поделать.\nИзвините за неудобства!\n\nPS: в chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">это исправили</a>',
		"u_emtleakf": 'попробуйте сделать так:\n<ul><li>нажмите <code>F5</code> для обновления страницы</li><li>затем включите опцию <code>🥔</code> (простой интерфейс) во вкладке загрузок<li>и повторите попытку</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">скоро должны починить</a> в этом аспекте',
		"u_s404": "не найдено на сервере",
		"u_expl": "объяснить",
		"u_maxconn": "в большинстве браузеров это нельзя поднять выше 6, но firefox позволяет увеличить лимит с помощью <code>connections-per-server</code> в <code>about:config</code>",
		"u_tu": '<p class="warn">ВНИМАНИЕ: активен режим турбо, <span>&nbsp;клиент может игнорировать незавершённые загрузки; подробнее при наведении на кнопку турбо</span></p>',
		"u_ts": '<p class="warn">ВНИМАНИЕ: активен режим турбо, <span>&nbsp;результаты поиска могут быть некорректными; подробнее при наведении на кнопку турбо</span></p>',
		"u_turbo_c": "режим турбо отключён сервером",
		"u_turbo_g": "отключаю турбо, поскольку у вас нет прав\nна просмотр папок в этом хранилище",
		"u_life_cfg": 'автоудаление через <input id="lifem" p="60" /> мин (или <input id="lifeh" p="3600" /> часов)',
		"u_life_est": 'загрузка будет удалена <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'эта папка требует\nавтоудаления файлов через {0}',
		"u_unp_ok": 'удаление разрешено для {0}',
		"u_unp_ng": 'удаление НЕ будет разрешено',
		"ue_ro": 'ваш доступ к данной папке - только чтение\n\n',
		"ue_nl": 'на данный момент вы не авторизованы',
		"ue_la": 'вы авторизованы как "{0}"',
		"ue_sr": 'сейчас вы в режиме поиска файлов\n\nперейдите в режим загрузки, нажав на лупу 🔎 (рядом с огромной кнопкой ИСКАТЬ), и попробуйте снова\n\nизвините',
		"ue_ta": 'попробуйте загрузить снова, теперь должно сработать',
		"ue_ab": "этот файл уже загружают в другую папку, та загрузка должна быть завершена перед тем, как загрузить этот же файл в другое место.\n\nВы можете отменить свою загрузку через 🧯 сверху слева",
		"ur_1uo": "OK: Файл успешно загружен",
		"ur_auo": "OK: Все {0} файлов успешно загружены",
		"ur_1so": "OK: Файл найден на сервере",
		"ur_aso": "OK: Все {0} файлов найдены на сервере",
		"ur_1un": "Загрузка не удалась, извините",
		"ur_aun": "Все {0} загрузок не удались, извините",
		"ur_1sn": "Файл НЕ был найден на сервере",
		"ur_asn": "Все {0} файлов НЕ было найдено на сервере",
		"ur_um": "Завершено;\n{0} успешно,\n{1} ошибок, извините",
		"ur_sm": "Завершено;\n{0} файлов найдено на сервере,\n{1} файлов НЕ найдено на сервере",

		"lang_set": "перезагрузить страницу, чтобы применить изменения?",
	},
	"spa": {
		"tt": "Español",

		"cols": {
			"c": "acciones",
			"dur": "duración",
			"q": "calidad / bitrate",
			"Ac": "códec de audio",
			"Vc": "códec de vídeo",
			"Fmt": "formato / contenedor",
			"Ahash": "checksum de audio",
			"Vhash": "checksum de vídeo",
			"Res": "resolución",
			"T": "tipo de archivo",
			"aq": "calidad de audio / bitrate",
			"vq": "calidad de vídeo / bitrate",
			"pixfmt": "submuestreo / estructura de píxel",
			"resw": "resolución horizontal",
			"resh": "resolución vertical",
			"chs": "canales de audio",
			"hz": "frecuencia de muestreo"
		},

		"hks": [
			[
				"varios",
				["ESC", "cerrar varias cosas"],

				"gestor de archivos",
				["G", "alternar vista de lista / cuadrícula"],
				["T", "alternar miniaturas / iconos"],
				["⇧ A/D", "tamaño de miniatura"],
				["ctrl-K", "eliminar seleccionados"],
				["ctrl-X", "cortar selección al portapapeles"],
				["ctrl-C", "copiar selección al portapapeles"],
				["ctrl-V", "pegar (mover/copiar) aquí"],
				["Y", "descargar seleccionados"],
				["F2", "renombrar seleccionados"],

				"selección en lista de archivos",
				["space", "alternar selección de archivo"],
				["↑/↓", "mover cursor de selección"],
				["ctrl ↑/↓", "mover cursor y vista"],
				["⇧ ↑/↓", "seleccionar anterior/siguiente archivo"],
				["ctrl-A", "seleccionar todos los archivos / carpetas"]
			], [
				"navegación",
				["B", "alternar breadcrumbs / panel de navegación"],
				["I/K", "anterior/siguiente carpeta"],
				["M", "carpeta de nivel superior (o contraer actual)"],
				["V", "alternar carpetas / archivos en panel de navegación"],
				["A/D", "tamaño del panel de navegación"]
			], [
				"reproductor de audio",
				["J/L", "anterior/siguiente canción"],
				["U/O", "saltar 10s atrás/adelante"],
				["0..9", "saltar a 0%..90%"],
				["P", "reproducir/pausar (también inicia)"],
				["S", "seleccionar canción en reproducción"],
				["Y", "descargar canción"]
			], [
				"visor de imágenes",
				["J/L, ←/→", "anterior/siguiente imagen"],
				["Home/End", "primera/última imagen"],
				["F", "pantalla completa"],
				["R", "rotar en sentido horario"],
				["⇧ R", "rotar en sentido antihorario"],
				["S", "seleccionar imagen"],
				["Y", "descargar imagen"]
			], [
				"reproductor de vídeo",
				["U/O", "saltar 10s atrás/adelante"],
				["P/K/Space", "reproducir/pausar"],
				["C", "continuar con el siguiente"],
				["V", "bucle"],
				["M", "silenciar"],
				["[ y ]", "establecer intervalo de bucle"]
			], [
				"visor de texto",
				["I/K", "anterior/siguiente archivo"],
				["M", "cerrar archivo"],
				["E", "editar archivo"],
				["S", "seleccionar archivo (para cortar/copiar/renombrar)"]
			]
		],

		"m_ok": "Aceptar",
		"m_ng": "Cancelar",

		"enable": "Activar",
		"danger": "PELIGRO",
		"clipped": "copiado al portapapeles",

		"ht_s1": "segundo",
		"ht_s2": "segundos",
		"ht_m1": "minuto",
		"ht_m2": "minutos",
		"ht_h1": "hora",
		"ht_h2": "horas",
		"ht_d1": "día",
		"ht_d2": "días",
		"ht_and": " y ",

		"goh": "panel de control",
		"gop": 'hermano anterior">anterior',
		"gou": 'carpeta de nivel superior">subir',
		"gon": 'siguiente carpeta">siguiente',
		"logout": "Cerrar sesión ",
		"login": "Iniciar sesión", //m
		"access": " acceso",
		"ot_close": "cerrar submenú",
		"ot_search": "buscar archivos por atributos, ruta / nombre, etiquetas de música, o cualquier combinación$N$N&lt;code&gt;foo bar&lt;/code&gt; = debe contener «foo» y «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = debe contener «foo» pero no «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = empieza con «yana» y es un archivo «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = contiene exactamente «try unite»$N$Nel formato de fecha es iso-8601, como$N&lt;code&gt;2009-12-31&lt;/code&gt; o &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "dessubir: elimina tus subidas recientes, o aborta las inacabadas",
		"ot_bup": "bup: uploader básico, soporta hasta netscape 4.0",
		"ot_mkdir": "mkdir: crear un nuevo directorio",
		"ot_md": "new-md: crear un nuevo documento markdown",
		"ot_msg": "msg: enviar un mensaje al registro del servidor",
		"ot_mp": "opciones del reproductor multimedia",
		"ot_cfg": "opciones de configuración",
		"ot_u2i": "up2k: subir archivos (si tienes acceso de escritura) o cambiar a modo de búsqueda para ver si existen en el servidor$N$Nlas subidas se pueden reanudar, usan múltiples hilos y conservan la fecha de los archivos, pero consume más CPU que [🎈]&nbsp; (el uploader básico)<br /><br />¡Durante las subidas, este icono se convierte en un indicador de progreso!",
		"ot_u2w": "up2k: subir archivos con soporte para reanudación (cierra tu navegador y arrastra los mismos archivos más tarde)$N$NMultihilo y conserva las fechas de los archivos, pero usa más CPU que [🎈]&nbsp; (el uploader básico)<br /><br />¡Durante las subidas, este icono se convierte en un indicador de progreso!",
		"ot_noie": "Por favor, usa Chrome / Firefox / Edge",

		"ab_mkdir": "crear directorio",
		"ab_mkdoc": "nuevo documento markdown",
		"ab_msg": "enviar msg al registro del servidor",

		"ay_path": "saltar a carpetas",
		"ay_files": "saltar a archivos",

		"wt_ren": "renombrar elementos seleccionados$NAtajo: F2",
		"wt_del": "eliminar elementos seleccionados$NAtajo: ctrl-K",
		"wt_cut": "cortar elementos seleccionados &lt;small&gt;(luego pegar en otro lugar)&lt;/small&gt;$NAtajo: ctrl-X",
		"wt_cpy": "copiar elementos seleccionados al portapapeles$N(para pegarlos en otro lugar)$NAtajo: ctrl-C",
		"wt_pst": "pegar una selección previamente cortada / copiada$NAtajo: ctrl-V",
		"wt_selall": "seleccionar todos los archivos$NAtajo: ctrl-A (con un archivo con foco)",
		"wt_selinv": "invertir selección",
		"wt_zip1": "descargar esta carpeta como un archivo comprimido",
		"wt_selzip": "descargar selección como archivo comprimido",
		"wt_seldl": "descargar selección como archivos separados$NAtajo: Y",
		"wt_npirc": "copiar información de pista en formato IRC",
		"wt_nptxt": "copiar información de pista en texto plano",
		"wt_m3ua": "añadir a lista m3u (haz clic en <code>📻copiar</code> después)",
		"wt_m3uc": "copiar lista m3u al portapapeles",
		"wt_grid": "alternar vista de cuadrícula / lista$NAtajo: G",
		"wt_prev": "pista anterior$NAtajo: J",
		"wt_play": "reproducir / pausar$NAtajo: P",
		"wt_next": "siguiente pista$NAtajo: L",

		"ul_par": "subidas paralelas:",
		"ut_rand": "aleatorizar nombres de archivo",
		"ut_u2ts": 'copiar la fecha de última modificación$Nde tu sistema de archivos al servidor">📅',
		"ut_ow": "sobrescribir archivos existentes en el servidor?$N🛡️: nunca (generará un nuevo nombre de archivo en su lugar)$N🕒: sobrescribir si el archivo del servidor es más antiguo que el tuyo$N♻️: siempre sobrescribir si los archivos son diferentes",
		"ut_mt": "continuar generando hashes de otros archivos mientras se sube$N$Nquizás desactivar si tu CPU o HDD es un cuello de botella",
		"ut_ask": 'pedir confirmación antes de iniciar la subida">💭',
		"ut_pot": "mejorar la velocidad de subida en dispositivos lentos$Nsimplificando la interfaz de usuario",
		"ut_srch": "no subir, en su lugar comprobar si los archivos ya $N existen en el servidor (escaneará todas las carpetas que puedas leer)",
		"ut_par": "pausar subidas poniéndolo a 0$N$Naumentar si tu conexión es lenta / de alta latencia$N$Nmantener en 1 en LAN o si el HDD del servidor es un cuello de botella",
		"ul_btn": "arrastra archivos / carpetas<br>aquí (o haz clic)",
		"ul_btnu": "S U B I R",
		"ul_btns": "B U S C A R",

		"ul_hash": "hash",
		"ul_send": "envio",
		"ul_done": "hecho",
		"ul_idle1": "aún no hay subidas en cola",
		"ut_etah": "velocidad media de &lt;em&gt;hashing&lt;/em&gt;, y tiempo estimado para finalizar",
		"ut_etau": "velocidad media de &lt;em&gt;subida&lt;/em&gt; y tiempo estimado para finalizar",
		"ut_etat": "velocidad media &lt;em&gt;total&lt;/em&gt; y tiempo estimado para finalizar",

		"uct_ok": "completado con éxito",
		"uct_ng": "fallido: error / rechazado / no encontrado",
		"uct_done": "éxitos y fallos combinados",
		"uct_bz": "generando hash o subiendo",
		"uct_q": "inactivo, pendiente",

		"utl_name": "nombre de archivo",
		"utl_ulist": "lista",
		"utl_ucopy": "copiar",
		"utl_links": "enlaces",
		"utl_stat": "estado",
		"utl_prog": "progreso",

		"utl_404": "404",
		"utl_err": "ERROR",
		"utl_oserr": "Error-SO",
		"utl_found": "encontrado",
		"utl_defer": "posponer",
		"utl_yolo": "YOLO",
		"utl_done": "hecho",

		"ul_flagblk": "los archivos se añadieron a la cola</b><br>sin embargo, hay un up2k ocupado en otra pestaña del navegador,<br>esperando a que termine primero",
		"ul_btnlk": "la configuración del servidor ha bloqueado esta opción en este estado",

		"udt_up": "Subir",
		"udt_srch": "Buscar",
		"udt_drop": "suéltalo aquí",

		"u_nav_m": "<h6>vale, ¿qué tienes?</h6><code>Intro</code> = Archivos (uno o más)\n<code>ESC</code> = Una carpeta (incluyendo subcarpetas)",
		"u_nav_b": "<a href=\"#\" id=\"modal-ok\">Archivos</a><a href=\"#\" id=\"modal-ng\">Una carpeta</a>",

		"cl_opts": "opciones",
		"cl_themes": "tema",
		"cl_langs": "idioma",
		"cl_ziptype": "descarga de carpeta",
		"cl_uopts": "opciones up2k",
		"cl_favico": "favicon",
		"cl_bigdir": "directorios grandes",
		"cl_hsort": "#ordenar",
		"cl_keytype": "notación musical",
		"cl_hiddenc": "columnas ocultas",
		"cl_hidec": "ocultar",
		"cl_reset": "restablecer",
		"cl_hpick": "toca en las cabeceras de columna para ocultarlas en la tabla de abajo",
		"cl_hcancel": "ocultación de columna cancelada",

		"ct_grid": '田 cuadrícula',
		"ct_ttips": '◔ ◡ ◔">ℹ️ tooltips',
		"ct_thumb": 'en vista de cuadrícula, alternar iconos o miniaturas$NAtajo: T">🖼️ miniaturas',
		"ct_csel": 'usa CTRL y SHIFT para seleccionar archivos en la vista de cuadrícula">sel',
		"ct_ihop": 'al cerrar el visor de imágenes, desplazarse hasta el último archivo visto">g⮯',
		"ct_dots": 'mostrar archivos ocultos (si el servidor lo permite)">archivos ocultos',
		"ct_qdel": 'al eliminar archivos, pedir confirmación solo una vez">elim. rápida',
		"ct_dir1st": 'ordenar carpetas antes que archivos">📁 primero',
		"ct_nsort": 'orden natural (para nombres de archivo con dígitos iniciales)">ord. natural',
		"ct_utc": 'use UTC para todas las horas">UTC', //m
		"ct_readme": 'mostrar README.md en los listados de carpetas">📜 léeme',
		"ct_idxh": 'mostrar index.html en lugar del listado de carpetas">htm',
		"ct_sbars": 'mostrar barra lateral">⟊',

		"cut_umod": 'si un archivo ya existe en el servidor, actualiza la fecha de última modificación del servidor para que coincida con tu archivo local (requiere permisos de escritura+eliminación)">re📅',

		"cut_turbo": 'el botón yolo, probablemente NO quieras activarlo:$N$Núsalo si estabas subiendo una gran cantidad de archivos y tuviste que reiniciar por alguna razón, y quieres continuar la subida lo antes posible$N$Nesto reemplaza la comprobación de hash por un simple <em>&quot;¿tiene este el mismo tamaño de archivo en el servidor?&quot;</em> así que si el contenido del archivo es diferente, NO se subirá$N$Ndeberías desactivar esto cuando la subida termine, y luego &quot;subir&quot; los mismos archivos de nuevo para que el cliente los verifique">turbo',

		"cut_datechk": 'no tiene efecto a menos que el botón turbo esté activado$N$Nreduce el factor yolo en una pequeña cantidad; comprueba si las fechas de los archivos en el servidor coinciden con las tuyas$N$N<em>teóricamente</em> debería detectar la mayoría de las subidas inacabadas / corruptas, pero no es un sustituto de hacer una pasada de verificación con el turbo desactivado después">verif. fecha',

		"cut_u2sz": "tamaño (en MiB) de cada trozo de subida; los valores grandes vuelan mejor a través del atlántico. Prueba valores bajos en conexiones muy poco fiables",

		"cut_flag": "asegura que solo una pestaña esté subiendo a la vez $N -- otras pestañas también deben tener esto activado $N -- solo afecta a pestañas en el mismo dominio",

		"cut_az": "subir archivos en orden alfabético, en lugar de los más pequeños primero$N$Nel orden alfabético puede facilitar la detección visual de si algo salió mal en el servidor, pero hace la subida ligeramente más lenta en fibra / LAN",

		"cut_nag": "notificación del SO cuando la subida se complete$N(solo si el navegador o la pestaña no están activos)",
		"cut_sfx": "alerta sonora cuando la subida se complete$N(solo si el navegador o la pestaña no están activos)",

		"cut_mt": 'usar multithreading para acelerar el hashing de archivos$N$Nesto usa web-workers y requiere$Nmás RAM (hasta 512 MiB extra)$N$Nhace https un 30% más rápido, http 4.5x más rápido">mt',

		"cut_wasm": 'usar wasm en lugar del hasher incorporado del navegador; mejora la velocidad en navegadores basados en chrome pero aumenta la carga de la CPU, y muchas versiones antiguas de chrome tienen errores que hacen que el navegador consuma toda la RAM y se bloquee si esto está activado">wasm',

		"cft_text": "texto del favicon (dejar en blanco y refrescar para desactivar)",
		"cft_fg": "color de primer plano",
		"cft_bg": "color de fondo",

		"cdt_lim": "número máximo de archivos a mostrar en una carpeta",
		"cdt_ask": "al llegar al final,$Nen lugar de cargar más archivos,$Npreguntar qué hacer",
		"cdt_hsort": "cuántas reglas de ordenación (&lt;code&gt;,sorthref&lt;/code&gt;) incluir en las URLs de medios. Ponerlo a 0 también ignorará las reglas de ordenación incluidas en los enlaces de medios al hacer clic en ellos",

		"tt_entree": "mostrar panel de navegación (barra lateral con árbol de directorios)$NAtajo: B",
		"tt_detree": "mostrar breadcrumbs$NAtajo: B",
		"tt_visdir": "desplazarse a la carpeta seleccionada",
		"tt_ftree": "alternar árbol de carpetas / archivos de texto$NAtajo: V",
		"tt_pdock": "mostrar carpetas de niveles superiores en un panel acoplado en la parte superior",
		"tt_dynt": "crecimiento automático a medida que el árbol se expande",
		"tt_wrap": "ajuste de línea",
		"tt_hover": "revelar líneas que se desbordan al pasar el ratón$N( rompe el desplazamiento a menos que el $N&nbsp; cursor esté en el margen izquierdo )",

		"ml_pmode": "al final de la carpeta...",
		"ml_btns": "acciones",
		"ml_tcode": "transcodificar",
		"ml_tcode2": "transcodificar a",
		"ml_tint": "tinte",
		"ml_eq": "ecualizador de audio",
		"ml_drc": "compresor de rango dinámico",

		"mt_loop": 'poner en bucle/repetir una canción">🔁',
		"mt_one": 'parar después de una canción">1️⃣',
		"mt_shuf": 'reproducir aleatoriamente las canciones en cada carpeta">🔀',
		"mt_aplay": 'reproducir automaticamente si hay un ID de canción en el enlace en el que hiciste clic para acceder al servidor$N$Ndesactivar esto también evitará que la URL de la página se actualice con IDs de canción al reproducir música, para prevenir la reproducción automática si se pierden estos ajustes pero la URL permanece">a▶',
		"mt_preload": 'empezar a cargar la siguiente canción cerca del final para una reproducción sin pausas">precarga',
		"mt_prescan": 'ir a la siguiente carpeta antes de que la última canción$Ntermine, manteniendo contento al navegador$Npara que no detenga la reproducción">nav',
		"mt_fullpre": 'intentar precargar la canción entera;$N✅ activar en conexiones <b>inestables</b>,$N❌ <b>desactivar</b> probablemente en conexiones lentas">completa',
		"mt_fau": 'en teléfonos, evitar que la música se detenga si la siguiente canción no se precarga lo suficientemente rápido (puede causar fallos en la visualización de etiquetas)">☕️',
		"mt_waves": 'barra de búsqueda con forma de onda:$Nmostrar la amplitud del audio en la barra de progreso">~s',
		"mt_npclip": 'mostrar botones para copiar al portapapeles la canción actual">/np',
		"mt_m3u_c": 'mostrar botones para copiar al portapapeles las$Ncanciones seleccionadas como entradas de lista m3u8">📻',
		"mt_octl": 'integración con SO (teclas multimedia / OSD)">ctl-so',
		"mt_oseek": 'permitir buscar a través de la integración con el SO$N$Nnota: en algunos dispositivos (iPhones),$Nesto reemplaza el botón de siguiente canción">búsqueda',
		"mt_oscv": 'mostrar carátula del álbum en OSD">arte',
		"mt_follow": 'mantener la pista en reproducción visible en pantalla">🎯',
		"mt_compact": 'controles compactos">⟎',
		"mt_uncache": 'limpiar caché &nbsp;(prueba esto si tu navegador guardó en caché$Nuna copia rota de una canción que se niega a reproducir)">limpiar caché',
		"mt_mloop": 'repetir la carpeta actual">🔁 bucle',
		"mt_mnext": 'cargar la siguiente carpeta y continuar">📂 sig',
		"mt_mstop": 'detener reproducción">⏸ parar',
		"mt_cflac": 'convertir flac / wav a {0}">flac',
		"mt_caac": 'convertir aac / m4a a {0}">aac',
		"mt_coth": 'convertir todos los demás (no mp3) a {0}">oth',
		"mt_c2opus": 'la mejor opción para ordenadores, portátiles, android">opus',
		"mt_c2owa": 'opus-weba, para iOS 17.5 y superior">owa',
		"mt_c2caf": 'opus-caf, para iOS 11 a 17">caf',
		"mt_c2mp3": 'usar en dispositivos muy antiguos">mp3',
		"mt_c2flac": "la mejor calidad de sonido,$Npero descargas muy grandes\">flac", //m
		"mt_c2wav": "reproducción sin comprimir (aún más grande)\">wav", //m
		"mt_c2ok": "bien, buena elección",
		"mt_c2nd": "ese no es el formato de salida recomendado para tu dispositivo, pero está bien",
		"mt_c2ng": "tu dispositivo no parece soportar este formato de salida, pero intentémoslo de todas formas",
		"mt_xowa": "hay errores en iOS que impiden la reproducción en segundo plano con este formato; por favor, usa caf o mp3 en su lugar",
		"mt_tint": "nivel de fondo (0-100) en la barra de búsqueda$Npara hacer el buffering menos molesto",
		"mt_eq": "activa el ecualizador y el control de ganancia;$N$Nganancia &lt;code&gt;0&lt;/code&gt; = volumen estándar 100% (sin modificar)$N$Nancho &lt;code&gt;1 &nbsp;&lt;/code&gt; = estéreo estándar (sin modificar)$Nancho &lt;code&gt;0.5&lt;/code&gt; = 50% de crossfeed izq-der$Nancho &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nganancia &lt;code&gt;-0.8&lt;/code&gt; y ancho &lt;code&gt;10&lt;/code&gt; = eliminación de voz :^)$N$Nactivar el ecualizador hace que los álbumes sin pausas sean completamente sin pausas, así que déjalo activado con todos los valores a cero (excepto ancho = 1) si eso te importa",
		"mt_drc": "activa el compresor de rango dinámico (aplanador de volumen / brickwaller); también activará el EQ para equilibrar el espagueti, así que pon todos los campos de EQ excepto 'ancho' a 0 si no lo quieres$N$Nbaja el volumen del audio por encima de THRESHOLD dB; por cada RATIO dB pasado THRESHOLD hay 1 dB de salida, así que los valores por defecto de umbral -24 y ratio 12 significan que nunca debería sonar más fuerte de -22 dB y es seguro aumentar la ganancia del ecualizador a 0.8, o incluso 1.8 con ATK 0 y un RLS enorme como 90 (solo funciona en firefox; RLS es máx. 1 en otros navegadores)$N$N(ver wikipedia, lo explican mucho mejor)",

		"mb_play": "reproducir",
		"mm_hashplay": "¿reproducir este archivo de audio?",
		"mm_m3u": "pulsa <code>Intro/Aceptar</code> para Reproducir\npulsa <code>ESC/Cancelar</code> para Editar",
		"mp_breq": "se necesita firefox 82+ o chrome 73+ o iOS 15+",
		"mm_bload": "cargando...",
		"mm_bconv": "convirtiendo a {0}, por favor espera...",
		"mm_opusen": "tu navegador no puede reproducir archivos aac / m4a;\nse ha activado la transcodificación a opus",
		"mm_playerr": "fallo de reproducción: ",
		"mm_eabrt": "El intento de reproducción fue cancelado",
		"mm_enet": "Tu conexión a internet es inestable",
		"mm_edec": "¿Este archivo está supuestamente corrupto?",
		"mm_esupp": "Tu navegador no entiende este formato de audio",
		"mm_eunk": "Error desconocido",
		"mm_e404": "No se pudo reproducir el audio; error 404: Archivo no encontrado.",
		"mm_e403": "No se pudo reproducir el audio; error 403: Acceso denegado.\n\nIntenta pulsar F5 para recargar, quizás se cerró tu sesión",
		"mm_e500": "No se pudo reproducir el audio; error 500: Revisa los registros del servidor.",
		"mm_e5xx": "No se pudo reproducir el audio; error del servidor ",
		"mm_nof": "no se encuentran más archivos de audio cerca",
		"mm_prescan": "Buscando música para reproducir a continuación...",
		"mm_scank": "Encontrada la siguiente canción:",
		"mm_uncache": "caché limpiada; todas las canciones se volverán a descargar en la próxima reproducción",
		"mm_hnf": "esa canción ya no existe",

		"im_hnf": "esa imagen ya no existe",

		"f_empty": "esta carpeta está vacía",
		"f_chide": "esto ocultará la columna «{0}»\n\npuedes volver a mostrar las columnas en la pestaña de configuración",
		"f_bigtxt": "este archivo pesa {0} MiB -- ¿realmente verlo como texto?",
		"f_bigtxt2": "¿ver solo el final del archivo en su lugar? esto también activará el seguimiento, mostrando las líneas de texto recién añadidas en tiempo real",
		"fbd_more": '<div id="blazy">mostrando <code>{0}</code> de <code>{1}</code> archivos; <a href="#" id="bd_more">mostrar {2}</a> o <a href="#" id="bd_all">mostrar todos</a></div>',
		"fbd_all": '<div id="blazy">mostrando <code>{0}</code> de <code>{1}</code> archivos; <a href="#" id="bd_all">mostrar todos</a></div>',
		"f_anota": "solo {0} de los {1} elementos fueron seleccionados;\npara seleccionar la carpeta completa, primero desplázate hasta el final",

		"f_dls": "los enlaces a archivos en la carpeta actual se han\nconvertido en enlaces de descarga",

		"f_partial": "Para descargar de forma segura un archivo que se está subiendo actualmente, por favor haz clic en el archivo con el mismo nombre, pero sin la extensión <code>.PARTIAL</code>. Por favor, pulsa CANCELAR o Escape para hacer esto.\n\nPulsar ACEPTAR o Intro ignorará esta advertencia y continuará descargando el archivo temporal <code>.PARTIAL</code>, lo que casi con toda seguridad te dará datos corruptos.",

		"ft_paste": "pegar {0} elementos$NAtajo: ctrl-V",
		"fr_eperm": "no se puede renombrar:\nno tienes permiso de “mover” en esta carpeta",
		"fd_eperm": "no se puede eliminar:\nno tienes permiso de “eliminar” en esta carpeta",
		"fc_eperm": "no se puede cortar:\nno tienes permiso de “mover” en esta carpeta",
		"fp_eperm": "no se puede pegar:\nno tienes permiso de “escribir” en esta carpeta",
		"fr_emore": "selecciona al menos un elemento para renombrar",
		"fd_emore": "selecciona al menos un elemento para eliminar",
		"fc_emore": "selecciona al menos un elemento para cortar",
		"fcp_emore": "selecciona al menos un elemento para copiar al portapapeles",

		"fs_sc": "compartir la carpeta en la que estás",
		"fs_ss": "compartir los archivos seleccionados",
		"fs_just1d": "no puedes seleccionar más de una carpeta,\no mezclar archivos y carpetas en una selección",
		"fs_abrt": "❌ abortar",
		"fs_rand": "🎲 nombre aleatorio",
		"fs_go": "✅ crear enlace",
		"fs_name": "nombre",
		"fs_src": "origen",
		"fs_pwd": "contraseña",
		"fs_exp": "caducidad",
		"fs_tmin": "minutos",
		"fs_thrs": "horas",
		"fs_tdays": "días",
		"fs_never": "eterno",
		"fs_pname": "nombre opcional del enlace; será aleatorio si se deja en blanco",
		"fs_tsrc": "el archivo o carpeta a compartir",
		"fs_ppwd": "contraseña opcional",
		"fs_w8": "creando enlace...",
		"fs_ok": "pulsa <code>Intro/Aceptar</code> para Copiar al Portapapeles\npulsa <code>ESC/Cancelar</code> para Cerrar",

		"frt_dec": "puede arreglar algunos casos de nombres de archivo rotos\">url-decode",
		"frt_rst": "restaurar los nombres de archivo modificados a los originales\">↺ restablecer",
		"frt_abrt": "abortar y cerrar esta ventana\">❌ cancelar",
		"frb_apply": "APLICAR RENOMBRADO",
		"fr_adv": "renombrado por lotes / metadatos / patrones\">avanzado",
		"fr_case": "regex sensible a mayúsculas\">mayús",
		"fr_win": "nombres seguros para windows; reemplaza <code>&lt;&gt;:&quot;\\|?*</code> con caracteres japoneses de ancho completo\">win",
		"fr_slash": "reemplaza <code>/</code> con un carácter que no cree nuevas carpetas\">sin /",
		"fr_re": "patrón de búsqueda regex para aplicar a los nombres de archivo originales; los grupos de captura se pueden referenciar en el campo de formato de abajo como &lt;code&gt;(1)&lt;/code&gt; y &lt;code&gt;(2)&lt;/code&gt; y así sucesivamente",
		"fr_fmt": "inspirado en foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; se reemplaza por el título de la canción,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; omite la parte [entre corchetes] si el artista está en blanco$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; rellena el número de pista a 2 dígitos",
		"fr_pdel": "eliminar",
		"fr_pnew": "guardar como",
		"fr_pname": "proporciona un nombre para tu nuevo preajuste",
		"fr_aborted": "abortado",
		"fr_lold": "nombre antiguo",
		"fr_lnew": "nombre nuevo",
		"fr_tags": "etiquetas para los archivos seleccionados (solo lectura, como referencia):",
		"fr_busy": "renombrando {0} elementos...\n\n{1}",
		"fr_efail": "fallo al renombrar:\n",
		"fr_nchg": "{0} de los nuevos nombres fueron alterados debido a <code>win</code> y/o <code>sin /</code>\n\n¿Aceptar para continuar con estos nuevos nombres alterados?",

		"fd_ok": "eliminación correcta",
		"fd_err": "fallo al eliminar:\n",
		"fd_none": "no se eliminó nada; quizás bloqueado por la configuración del servidor (xbd)?",
		"fd_busy": "eliminando {0} elementos...\n\n{1}",
		"fd_warn1": "¿ELIMINAR estos {0} elementos?",
		"fd_warn2": "<b>¡Última oportunidad!</b> No se puede deshacer. ¿Eliminar?",

		"fc_ok": "cortados {0} elementos",
		"fc_warn": "cortados {0} elementos\n\npero: solo <b>esta</b> pestaña del navegador puede pegarlos\n(dado que la selección es absolutamente masiva)",

		"fcc_ok": "copiados {0} elementos al portapapeles",
		"fcc_warn": "copiados {0} elementos al portapapeles\n\npero: solo <b>esta</b> pestaña del navegador puede pegarlos\n(dado que la selección es absolutamente masiva)",

		"fp_apply": "usar estos nombres",
		"fp_ecut": "primero corta o copia algunos archivos / carpetas para pegar / mover\n\nnota: puedes cortar / pegar entre diferentes pestañas del navegador",
		"fp_ename": "{0} elementos no se pueden mover aquí porque los nombres ya existen. Dales nuevos nombres abajo para continuar, o deja el nombre en blanco para omitirlos:",
		"fcp_ename": "{0} elementos no se pueden copiar aquí porque los nombres ya existen. Dales nuevos nombres abajo para continuar, o deja el nombre en blanco para omitirlos:",
		"fp_emore": "todavía quedan algunas colisiones de nombres por resolver",
		"fp_ok": "movimiento correcto",
		"fcp_ok": "copia correcta",
		"fp_busy": "moviendo {0} elementos...\n\n{1}",
		"fcp_busy": "copiando {0} elementos...\n\n{1}",
		"fp_abrt": "cancelando...", //m
		"fp_err": "fallo al mover:\n",
		"fcp_err": "fallo al copiar:\n",
		"fp_confirm": "¿mover estos {0} elementos aquí?",
		"fcp_confirm": "¿copiar estos {0} elementos aquí?",
		"fp_etab": "fallo al leer el portapapeles de otra pestaña del navegador",
		"fp_name": "subiendo un archivo desde tu dispositivo. Dale un nombre:",
		"fp_both_m": "<h6>elige qué pegar</h6><code>Intro</code> = Mover {0} archivos desde «{1}»\n<code>ESC</code> = Subir {2} archivos desde tu dispositivo",
		"fcp_both_m": "<h6>elige qué pegar</h6><code>Intro</code> = Copiar {0} archivos desde «{1}»\n<code>ESC</code> = Subir {2} archivos desde tu dispositivo",
		"fp_both_b": "<a href=\"#\" id=\"modal-ok\">Mover</a><a href=\"#\" id=\"modal-ng\">Subir</a>",
		"fcp_both_b": "<a href=\"#\" id=\"modal-ok\">Copiar</a><a href=\"#\" id=\"modal-ng\">Subir</a>",

		"mk_noname": "escribe un nombre en el campo de texto de la izquierda antes de hacer eso :p",

		"tv_load": "Cargando documento de texto:\n\n{0}\n\n{1}% ({2} de {3} MiB cargados)",
		"tv_xe1": "no se pudo cargar el archivo de texto:\n\nerror ",
		"tv_xe2": "404, archivo no encontrado",
		"tv_lst": "lista de archivos de texto en",
		"tvt_close": "volver a la vista de carpetas$NAtajo: M (o Esc)\">❌ cerrar",
		"tvt_dl": "descargar este archivo$NAtajo: Y\">💾 descargar",
		"tvt_prev": "mostrar documento anterior$NAtajo: i\">⬆ ant",
		"tvt_next": "mostrar siguiente documento$NAtajo: K\">⬇ sig",
		"tvt_sel": "seleccionar archivo &nbsp; ( para cortar / copiar / eliminar / ... )$NAtajo: S\">sel",
		"tvt_edit": "abrir archivo en editor de texto$NAtajo: E\">✏️ editar",
		"tvt_tail": "monitorizar cambios en el archivo; mostrar nuevas líneas en tiempo real\">📡 seguir",
		"tvt_wrap": "ajuste de línea\">↵",
		"tvt_atail": "bloquear el desplazamiento al final de la página\">⚓",
		"tvt_ctail": "decodificar colores de terminal (códigos de escape ansi)\">🌈",
		"tvt_ntail": "límite de historial (cuántos bytes de texto mantener cargados)",

		"m3u_add1": "canción añadida a la lista m3u",
		"m3u_addn": "{0} canciones añadidas a la lista m3u",
		"m3u_clip": "lista m3u copiada al portapapeles\n\ndebes crear un nuevo archivo de texto llamado algo.m3u y pegar la lista en ese documento; esto lo hará reproducible",

		"gt_vau": "no mostrar vídeos, solo reproducir el audio\">🎧",
		"gt_msel": "activar selección de archivos; ctrl-clic en un archivo para anular$N$N&lt;em&gt;cuando está activo: doble clic en un archivo / carpeta para abrirlo&lt;/em&gt;$N$NAtajo: S\">multiselección",
		"gt_crop": "recortar miniaturas\">recortar",
		"gt_3x": "miniaturas de alta resolución\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "recortar",
		"gt_sort": "ordenar por",
		"gt_name": "nombre",
		"gt_sz": "tamaño",
		"gt_ts": "fecha",
		"gt_ext": "tipo",
		"gt_c1": "truncar más los nombres de archivo (mostrar menos)",
		"gt_c2": "truncar menos los nombres de archivo (mostrar más)",

		"sm_w8": "buscando...",
		"sm_prev": "los resultados de búsqueda a continuación son de una consulta anterior:\n  ",
		"sl_close": "cerrar resultados de búsqueda",
		"sl_hits": "mostrando {0} resultados",
		"sl_moar": "cargar más",

		"s_sz": "tamaño",
		"s_dt": "fecha",
		"s_rd": "ruta",
		"s_fn": "nombre",
		"s_ta": "etiquetas",
		"s_ua": "subido@",
		"s_ad": "avanzado",
		"s_s1": "MiB mínimo",
		"s_s2": "MiB máximo",
		"s_d1": "mín. iso8601",
		"s_d2": "máx. iso8601",
		"s_u1": "subido después de",
		"s_u2": "y/o antes de",
		"s_r1": "la ruta contiene &nbsp; (separado por espacios)",
		"s_f1": "el nombre contiene &nbsp; (negar con -no)",
		"s_t1": "las etiquetas contienen &nbsp; (^=inicio, fin=$)",
		"s_a1": "propiedades de metadatos específicas",

		"md_eshow": "no se puede renderizar ",
		"md_off": "[📜<em>léeme</em>] desactivado en [⚙️] -- documento oculto",

		"badreply": "Fallo al procesar la respuesta del servidor",

		"xhr403": "403: Acceso denegado\n\nintenta pulsar F5, quizás se cerró tu sesión",
		"xhr0": "desconocido (probablemente se perdió la conexión con el servidor, o el servidor está desconectado)",
		"cf_ok": "perdón por eso -- la protección DD" + wah + "oS se activó\n\nlas cosas deberían reanudarse en unos 30 segundos\n\nsi no pasa nada, pulsa F5 para recargar la página",
		"tl_xe1": "no se pudieron listar las subcarpetas:\n\nerror ",
		"tl_xe2": "404: Carpeta no encontrada",
		"fl_xe1": "no se pudieron listar los archivos en la carpeta:\n\nerror ",
		"fl_xe2": "404: Carpeta no encontrada",
		"fd_xe1": "no se pudo crear la subcarpeta:\n\nerror ",
		"fd_xe2": "404: Carpeta de nivel superior no encontrada",
		"fsm_xe1": "no se pudo enviar el mensaje:\n\nerror ",
		"fsm_xe2": "404: Carpeta de nivel superior no encontrada",
		"fu_xe1": "fallo al cargar la lista de deshacer del servidor:\n\nerror ",
		"fu_xe2": "404: ¿Archivo no encontrado?",

		"fz_tar": "archivo gnu-tar sin comprimir (linux / mac)",
		"fz_pax": "tar formato pax sin comprimir (más lento)",
		"fz_targz": "gnu-tar con compresión gzip nivel 3$N$Nesto suele ser muy lento, así que$Nusa tar sin comprimir en su lugar",
		"fz_tarxz": "gnu-tar con compresión xz nivel 1$N$Nesto suele ser muy lento, así que$Nusa tar sin comprimir en su lugar",
		"fz_zip8": "zip con nombres de archivo utf8 (puede dar problemas en windows 7 y anteriores)",
		"fz_zipd": "zip con nombres de archivo cp437 tradicionales, para software muy antiguo",
		"fz_zipc": "cp437 con crc32 calculado tempranamente,$Npara MS-DOS PKZIP v2.04g (octubre 1993)$N(tarda más en procesar antes de que la descarga pueda empezar)",

		"un_m1": "puedes eliminar tus subidas recientes (o abortar las inacabadas) a continuación",
		"un_upd": "actualizar",
		"un_m4": "o compartir los archivos visibles a continuación:",
		"un_ulist": "mostrar",
		"un_ucopy": "copiar",
		"un_flt": "filtro opcional:&nbsp; la URL debe contener",
		"un_fclr": "limpiar filtro",
		"un_derr": "fallo al deshacer-eliminar:\n",
		"un_f5": "algo se rompió, por favor intenta actualizar o pulsa F5",
		"un_uf5": "lo siento pero tienes que refrescar la página (por ejemplo pulsando F5 o CTRL-R) antes de que esta subida pueda ser abortada",
		"un_nou": "<b>aviso:</b> servidor demasiado ocupado para mostrar subidas inacabadas; haz clic en el enlace \"actualizar\" en un momento",
		"un_noc": "<b>aviso:</b> la opción de deshacer subidas completadas no está activada/permitida en la configuración del servidor",
		"un_max": "mostrando los primeros 2000 archivos (usa el filtro)",
		"un_avail": "{0} subidas recientes se pueden eliminar<br />{1} inacabadas se pueden abortar",
		"un_m2": "ordenado por tiempo de subida; más recientes primero:",
		"un_no1": "¡pues no! ninguna subida es suficientemente reciente",
		"un_no2": "¡pues no! ninguna subida que coincida con ese filtro es suficientemente reciente",
		"un_next": "eliminar los siguientes {0} archivos a continuación",
		"un_abrt": "abortar",
		"un_del": "eliminar",
		"un_m3": "cargando tus subidas recientes...",
		"un_busy": "eliminando {0} archivos...",
		"un_clip": "{0} enlaces copiados al portapapeles",

		"u_https1": "deberías",
		"u_https2": "cambiar a https",
		"u_https3": "para un mejor rendimiento",
		"u_ancient": "tu navegador es impresionantemente antiguo -- quizás deberías <a href=\"#\" onclick=\"goto('bup')\">usar bup en su lugar</a>",
		"u_nowork": "se necesita firefox 53+ o chrome 57+ o iOS 11+",
		"tail_2old": "se necesita firefox 105+ o chrome 71+ o iOS 14.5+",
		"u_nodrop": "tu navegador es demasiado antiguo para subir arrastrando y soltando",
		"u_notdir": "¡eso no es una carpeta!\n\ntu navegador es demasiado antiguo,\npor favor intenta arrastrar y soltar en su lugar",
		"u_uri": "para arrastrar y soltar imágenes desde otras ventanas del navegador,\npor favor suéltalas sobre el gran botón de subida",
		"u_enpot": "cambiar a <a href=\"#\">UI ligera</a> (puede mejorar la velocidad de subida)",
		"u_depot": "cambiar a <a href=\"#\">UI elegante</a> (puede reducir la velocidad de subida)",
		"u_gotpot": "cambiando a la UI ligera para mejorar la velocidad de subida,\n\n¡siéntete libre de no estar de acuerdo y volver a cambiar!",
		"u_pott": "<p>archivos: &nbsp; <b>{0}</b> finalizados, &nbsp; <b>{1}</b> fallidos, &nbsp; <b>{2}</b> ocupados, &nbsp; <b>{3}</b> en cola</p>",
		"u_ever": "este es el uploader básico; up2k necesita al menos<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": "este es el uploader básico; <a href=\"#\" id=\"u2yea\">up2k</a> es mejor",
		"u_uput": "optimizar para velocidad (omitir checksum)",
		"u_ewrite": "no tienes acceso de escritura a esta carpeta",
		"u_eread": "no tienes acceso de lectura a esta carpeta",
		"u_enoi": "la búsqueda de archivos no está activada en la configuración del servidor",
		"u_enoow": "sobrescribir no funcionará aquí; se necesita permiso de eliminación",
		"u_badf": "Estos {0} archivos (de un total de {1}) se omitieron, posiblemente debido a permisos del sistema de archivos:\n\n",
		"u_blankf": "Estos {0} archivos (de un total de {1}) están en blanco / vacíos; ¿subirlos de todos modos?\n\n",
		"u_applef": "Estos {0} archivos (de un total de {1}) probablemente no son deseables;\nPulsa <code>Aceptar/Intro</code> para OMITIR los siguientes archivos,\nPulsa <code>Cancelar/ESC</code> para NO excluir, y SUBIR esos también:\n\n",
		"u_just1": "\nQuizás funcione mejor si seleccionas solo un archivo",
		"u_ff_many": "si usas <b>Linux / MacOS / Android,</b> esta cantidad de archivos <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>podría</em> bloquear Firefox!</a>\nsi eso ocurre, por favor inténtalo de nuevo (o usa Chrome).",
		"u_up_life": "Esta subida será eliminada del servidor\n{0} después de que se complete",
		"u_asku": "subir estos {0} archivos a <code>{1}</code>",
		"u_unpt": "puedes deshacer / eliminar esta subida usando el 🧯 de arriba a la izquierda",
		"u_bigtab": "a punto de mostrar {0} archivos\n\nesto podría bloquear tu navegador, ¿estás seguro?",
		"u_scan": "Escaneando archivos...",
		"u_dirstuck": "el iterador de directorios se atascó intentando acceder a los siguientes {0} elementos; se omitirán:",
		"u_etadone": "Hecho ({0}, {1} archivos)",
		"u_etaprep": "(preparando para subir)",
		"u_hashdone": "hashing completado",
		"u_hashing": "hash",
		"u_hs": "negociando...",
		"u_started": "los archivos se están subiendo ahora; mira en [🚀]",
		"u_dupdefer": "duplicado; se procesará después de todos los demás archivos",
		"u_actx": "haz clic en este texto para evitar la pérdida de<br />rendimiento al cambiar a otras ventanas/pestañas",
		"u_fixed": "¡OK!&nbsp; Arreglado 👍",
		"u_cuerr": "fallo al subir el trozo {0} de {1};\nprobablemente inofensivo, continuando\n\narchivo: {2}",
		"u_cuerr2": "el servidor rechazó la subida (trozo {0} de {1});\nse reintentará más tarde\n\narchivo: {2}\n\nerror ",
		"u_ehstmp": "se reintentará; mira abajo a la derecha",
		"u_ehsfin": "el servidor rechazó la solicitud para finalizar la subida; reintentando...",
		"u_ehssrch": "el servidor rechazó la solicitud para realizar la búsqueda; reintentando...",
		"u_ehsinit": "el servidor rechazó la solicitud para iniciar la subida; reintentando...",
		"u_eneths": "error de red al realizar la negociación de subida; reintentando...",
		"u_enethd": "error de red al comprobar la existencia del destino; reintentando...",
		"u_cbusy": "esperando a que el servidor vuelva a confiar en nosotros después de un fallo de red...",
		"u_ehsdf": "¡el servidor se quedó sin espacio en disco!\n\nse seguirá reintentando, por si alguien\nlibera suficiente espacio para continuar",
		"u_emtleak1": "parece que tu navegador podría tener una fuga de memoria;\npor favor",
		"u_emtleak2": " <a href=\"{0}\">cambia a https (recomendado)</a> o ",
		"u_emtleak3": " ",
		"u_emtleakc": "prueba lo siguiente:\n<ul><li>pulsa <code>F5</code> para refrescar la página</li><li>luego desactiva el botón &nbsp;<code>mt</code>&nbsp; en los &nbsp;<code>⚙️ ajustes</code></li><li>e intenta esa subida de nuevo</li></ul>Las subidas serán un poco más lentas, pero bueno.\n¡Perdón por las molestias!\n\nPD: chrome v107 <a href=\"https://bugs.chromium.org/p/chromium/issues/detail?id=1354816\" target=\"_blank\">tiene una solución</a> para esto",
		"u_emtleakf": "prueba lo siguiente:\n<ul><li>pulsa <code>F5</code> para refrescar la página</li><li>luego activa <code>🥔</code> (ligera) en la interfaz de subida</li><li>e intenta esa subida de nuevo</li></ul>\nPD: firefox <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\">con suerte tendrá una solución</a> en algún momento",
		"u_s404": "no encontrado en el servidor",
		"u_expl": "explicar",
		"u_maxconn": "la mayoría de los navegadores limitan esto a 6, pero firefox te permite aumentarlo con <code>connections-per-server</code> en <code>about:config</code>",
		"u_tu": '<p class="warn">AVISO: turbo activado, <span>&nbsp;el cliente puede no detectar y reanudar subidas incompletas; ver tooltip del botón turbo</span></p>',
		"u_ts": '<p class="warn">AVISO: turbo activado, <span>&nbsp;los resultados de búsqueda pueden ser incorrectos; ver tooltip del botón turbo</span></p>',
		"u_turbo_c": "turbo está desactivado en la configuración del servidor",
		"u_turbo_g": "desactivando turbo porque no tienes\nprivilegios para listar directorios en este volumen",
		"u_life_cfg": 'autoeliminar después de <input id="lifem" p="60" /> min (o <input id="lifeh" p="3600" /> horas)',
		"u_life_est": 'la subida se eliminará <span id="lifew" tt="hora local">---</span>',
		"u_life_max": "esta carpeta impone una\nvida máxima de {0}",
		"u_unp_ok": "se permite deshacer la subida durante {0}",
		"u_unp_ng": "NO se permitirá deshacer la subida",
		"ue_ro": "tu acceso a esta carpeta es de solo lectura\n\n",
		"ue_nl": "actualmente no has iniciado sesión",
		"ue_la": "actualmente has iniciado sesión como \"{0}\"",
		"ue_sr": "actualmente estás en modo de búsqueda de archivos\n\ncambia a modo de subida haciendo clic en la lupa 🔎 (junto al gran botón BUSCAR), e intenta subir de nuevo\n\nlo siento",
		"ue_ta": "intenta subir de nuevo, ahora debería funcionar",
		"ue_ab": "este archivo ya se está subiendo a otra carpeta, y esa subida debe completarse antes de que el archivo pueda ser subido a otro lugar.\n\nPuedes abortar y olvidar la subida inicial usando el 🧯 de arriba a la izquierda",
		"ur_1uo": "OK: Archivo subido con éxito",
		"ur_auo": "OK: Todos los {0} archivos subidos con éxito",
		"ur_1so": "OK: Archivo encontrado en el servidor",
		"ur_aso": "OK: Todos los {0} archivos encontrados en el servidor",
		"ur_1un": "Subida fallida, lo siento",
		"ur_aun": "Todas las {0} subidas fallaron, lo siento",
		"ur_1sn": "El archivo NO se encontró en el servidor",
		"ur_asn": "Los {0} archivos NO se encontraron en el servidor",
		"ur_um": "Finalizado;\n{0} subidas OK,\n{1} subidas fallidas, lo siento",
		"ur_sm": "Finalizado;\n{0} archivos encontrados en el servidor,\n{1} archivos NO encontrados en el servidor",

		"lang_set": "¿refrescar para que el cambio surta efecto?"
	},
	"swe": {
		"tt": "Svenska",

		"cols": {
			"c": "aktion",
			"dur": "längd",
			"q": "kvalitet / bitrate",
			"Ac": "ljudkodek",
			"Vc": "videokodek",
			"Fmt": "format / container",
			"Ahash": "ljudchecksumma",
			"Vhash": "videochecksumma",
			"Res": "upplösning",
			"T": "filtyp",
			"aq": "ljudkvalitet / bitrate",
			"vq": "videokvalitet / bitrate",
			"pixfmt": "subsampling / pixelstruktur",
			"resw": "horisontell upplösning",
			"resh": "vertikal upplösning",
			"chs": "antal ljudkanaler",
			"hz": "samplingsfrekvens"
		},

		"hks": [
			[
				"övrigt",
				["ESC", "stäng diverse paneler"],

				"filhanterare",
				["G", "växla mellan listvy / rutnät"],
				["T", "växla mellan miniatyrer / ikoner"],
				["⇧ A/D", "miniatyrstorlek"],
				["ctrl-K", "radera urval"],
				["ctrl-X", "klipp urval till urklipp"],
				["ctrl-C", "kopiera urval till urklipp"],
				["ctrl-V", "klistra in (kopiera/flytta) hit"],
				["Y", "ladda ner urval"],
				["F2", "byt namn på urval"],

				"välja filer",
				["Blanksteg", "växla val av fil"],
				["↑/↓", "flytta filvalsmarkör"],
				["ctrl ↑/↓", "flytta markör och vy"],
				["⇧ ↑/↓", "välj föregående/nästa fil"],
				["ctrl-A", "välj alla filer / mappar"],
			], [
				"navigation",
				["B", "växla mellan brödsmulor / trädvy"],
				["I/K", "föregående/nästa mapp"],
				["M", "hoppa till överordnad mapp (eller kollapsa närvarande)"],
				["V", "växla mellan mappar / textfiler i trädvy"],
				["A/D", "trädvystorlek"],
			], [
				"ljudspelare",
				["J/L", "föregående/nästa låt"],
				["U/O", "hoppa 10sek bakåt/framåt"],
				["0..9", "hoppa till 0%..90%"],
				["P", "play/paus (startar även uppspelning)"],
				["S", "välj låten som spelas"],
				["Y", "ladda ner låt"],
			], [
				"bildvisare",
				["J/L, ←/→", "föregående/nästa bild"],
				["Hem/End", "första/sista bilden"],
				["F", "helskärm"],
				["R", "rotera medsols"],
				["⇧ R", "rotera motsols"],
				["S", "välj bild"],
				["Y", "ladda ner bild"],
			], [
				"videospelare",
				["U/O", "hoppa 10sek bakåt/framåt"],
				["P/K/Blanksteg", "play/paus"],
				["C", "fortsätt med nästa"],
				["V", "loopa"],
				["M", "stäng av ljud"],
				["[ och ]", "ställ in loopintervall"],
			], [
				"textfilsvisare",
				["I/K", "föregående/nästa fil"],
				["M", "stäng textfil"],
				["E", "redigera textfil"],
				["S", "välj fil"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Avbryt",

		"enable": "Aktivera",
		"danger": "VARNING",
		"clipped": "kopierat till urklipp",

		"ht_s1": "sekund",
		"ht_s2": "sekunder",
		"ht_m1": "minut",
		"ht_m2": "minuter",
		"ht_h1": "timme",
		"ht_h2": "timmar",
		"ht_d1": "dag",
		"ht_d2": "dagar",
		"ht_and": " och ",

		"goh": "kontrollpanel",
		"gop": 'föregående mapp">föreg.',
		"gou": 'överordnad mapp">upp',
		"gon": 'nästa mapp">nästa',
		"logout": "Logga ut ",
		"login": "Logga in", //m
		"access": "-rättighet",
		"ot_close": "stäng undermeny",
		"ot_search": "sök efter filer via attribut, sökväg / namn, musiktaggar, eller någon kombination av dessa$N$N&lt;code&gt;foo bar&lt;/code&gt; = måste innehålla både «foo» och «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = måste innehålla «foo» men inte «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = måste börja med «yana» och vara en «opus»-fil$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = måste innehålla exakt «try unite»$N$Ndatumformatet är iso-8601, t.ex.$N&lt;code&gt;2009-12-31&lt;/code&gt; eller &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: radera dina senaste uppladdningar, eller avbryt pågående sådana",
		"ot_bup": "bup: enkel uppladdare, stödjer t o m netscape 4.0",
		"ot_mkdir": "mkdir: skapa en ny mapp",
		"ot_md": "new-md: skapa ett nytt markdown-dokument",
		"ot_msg": "msg: skicka ett meddelande till serverloggen",
		"ot_mp": "mediaspelarinställningar",
		"ot_cfg": "konfigurationsinställningar",
		"ot_u2i": 'up2k: ladda upp filer (om du har skrivrättigheter) eller byt till sökläge för att se om de finns någonstans på servern$N$Nuppladdningarna är återupptagbara, multitrådade och filernas tidsstämpel bevaras, men den använder mer CPU än [🎈]&nbsp; (den enkla uppladdaren)<br /><br />under uppladdningens gång blir denna ikon en förloppsindikator!',
		"ot_u2w": 'up2k: ladda upp filer med stöd för återupptagning (stäng din webbläsare och dra in samma filer senare)$N$Nmultitrådad och filernas tidsstämpel bevaras, men den använder mer CPU än [🎈]&nbsp; (den enkla uppladdaren)<br /><br />under uppladdningens gång blir denna ikon en förloppsindikator!',
		"ot_noie": 'Var vänlig använd Chrome / Firefox / Edge',

		"ab_mkdir": "skapa mapp",
		"ab_mkdoc": "nytt markdown-dokument",
		"ab_msg": "skicka medd. till serverlogg",

		"ay_path": "hoppa till mappar",
		"ay_files": "hoppa till filer",

		"wt_ren": "byt namn på urval$NSnabbtangent: F2",
		"wt_del": "radera urval$NSnabbtangent: ctrl-K",
		"wt_cut": "klipp urval&lt;small&gt;(för att klistra in någonstans)&lt;/small&gt;$NSnabbtangent: ctrl-X",
		"wt_cpy": "kopiera urval till urklipp$N(för att klistra in någonstans)$NSnabbtangent: ctrl-C",
		"wt_pst": "klistra in tidigare urval$NSnabbtangent: ctrl-V",
		"wt_selall": "välj alla filer$NSnabbtangent: ctrl-A (när en fil har fokus)",
		"wt_selinv": "invertera urval",
		"wt_zip1": "ladda ner denna mapp som ett arkiv",
		"wt_selzip": "ladda ner urval som ett arkiv",
		"wt_seldl": "ladda ner urval som separata filer$NSnabbtangent: Y",
		"wt_npirc": "kopiera IRC-formatterad låtinfo",
		"wt_nptxt": "kopiera låtinfo i klartext",
		"wt_m3ua": "lägg till i m3u-spellista (klicka på <code>📻copy</code> senare)",
		"wt_m3uc": "kopiera m3u-spellista till urklipp",
		"wt_grid": "växla mellan rutnät och listvy$NSnabbtangent: G",
		"wt_prev": "föregående låt$NSnabbtangent: J",
		"wt_play": "play / paus$NSnabbtangent: P",
		"wt_next": "nästa låt$NSnabbtangent: L",

		"ul_par": "samtidiga uppladdningar:",
		"ut_rand": "slumpa filnamn",
		"ut_u2ts": "bevara tidsstämpeln för senaste ändring$Nfrån ditt filsystem till servern\">📅",
		"ut_ow": "skriv över existerande filer på servern?$N🛡️: aldrig (skapar ett nytt filnamn istället)$N🕒: skriv över om serverns fil är äldre än din$N♻️: skriv alltid över om filerna skiljer sig",
		"ut_mt": "fortsätt hasha filer under uppladdningens gång$N$Nstäng av om din CPU eller disk är en flaskhals",
		"ut_ask": 'bekräfta innan uppladdningar påbörjas">💭',
		"ut_pot": "förbättra uppladdningshastigheten på långsamma enheter$Ngenom att förenkla användargränssnittet",
		"ut_srch": "ladda inte upp; kolla istället om filerna redan existerar på $N servern (detta kommer att skanna alla mappar med läsrättighet)",
		"ut_par": "du kan pausa all uppladdning genom att sätta detta till 0$N$Nöka denna om din uppkoppling är långsam eller har hög latens$N$Nsätt till 1 över lokala nätverk eller om serverns disk är en flaskhals",
		"ul_btn": "släpp filer / mappar<br>här (eller klicka)",
		"ul_btnu": "L A D D A  U P P",
		"ul_btns": "S Ö K",

		"ul_hash": "hashar",
		"ul_send": "skickar",
		"ul_done": "klar",
		"ul_idle1": "inga uppladdningar har köats",
		"ut_etah": "medelhastighet för &lt;em&gt;hashning&lt;/em&gt;, och uppskattad återstående tid",
		"ut_etau": "medelhastighet för &lt;em&gt;överföring&lt;/em&gt;, och uppskattad återstående tid",
		"ut_etat": "&lt;em&gt;total&lt;/em&gt; medelhastighet, och uppskattad återstående tid",

		"uct_ok": "lyckade",
		"uct_ng": "no-good: misslyckade / avvisade / ej funna",
		"uct_done": "ok och ng kombinerat",
		"uct_bz": "pågående",
		"uct_q": "köade",

		"utl_name": "filnamn",
		"utl_ulist": "visa",
		"utl_ucopy": "kopiera",
		"utl_links": "länkar",
		"utl_stat": "status",
		"utl_prog": "förlopp",

		// keep short:
		"utl_404": "404",
		"utl_err": "FEL",
		"utl_oserr": "OS-fel",
		"utl_found": "hittad",
		"utl_defer": "väntar",
		"utl_yolo": "YOLO",
		"utl_done": "klar",

		"ul_flagblk": "filerna lades till i kön,</b><br>men det finns en upptagen up2k i en annan webbläsarflik,<br>så vi väntar på den först",
		"ul_btnlk": "serverkonfigurationen har låst denna inställning",

		"udt_up": "Ladda upp",
		"udt_srch": "Sök",
		"udt_drop": "släpp här",

		"u_nav_m": '<h6>jaha, vad har du då?</h6><code>Enter</code> = Filer (en eller flera)\n<code>ESC</code> = En mapp (inklusive undermappar)',
		"u_nav_b": '<a href="#" id="modal-ok">Filer</a><a href="#" id="modal-ng">En mapp</a>',

		"cl_opts": "växlar",
		"cl_themes": "tema",
		"cl_langs": "språk",
		"cl_ziptype": "mappnedladdning",
		"cl_uopts": "up2k-inställningar",
		"cl_favico": "favikon",
		"cl_bigdir": "stora mappar",
		"cl_hsort": "#sort.",
		"cl_keytype": "tonartsnotering",
		"cl_hiddenc": "dolda kolumner",
		"cl_hidec": "dölj",
		"cl_reset": "återställ",
		"cl_hpick": "tryck på en kolumntitel för att dölja den i filvyn",
		"cl_hcancel": "kolumndöljning avbruten",

		"ct_grid": '田 rutnätet',
		"ct_ttips": '◔ ◡ ◔">ℹ️ tips',
		"ct_thumb": 'växla mellan miniatyrer och ikoner i rutnätsvyn$NSnabbtangent: T">🖼️ miniatyrer',
		"ct_csel": 'använd CTRL och SKIFT för urval av filer i rutnätsvyn">val',
		"ct_ihop": 'skrolla till den senast visade filen när bildvisaren stängs">g⮯',
		"ct_dots": 'visa dolda filer (om servern tillåter detta)">dolda',
		"ct_qdel": 'bekräfta endast en gång när filer raderas">srad',
		"ct_dir1st": 'sortera mappar före filer">📁 först',
		"ct_nsort": 'naturlig sortering (för filnamn med ledande siffror)">nsort',
		"ct_utc": 'visa alla datum och tider i UTC">UTC',
		"ct_readme": 'visa README.md i listvyn">📜 läsmig',
		"ct_idxh": 'visa index.html istället för listvyn">htm',
		"ct_sbars": 'visa rullningslister">⟊',

		"cut_umod": "om en fil redan existerar på servern, uppdatera serverns senast modifierade tidsstämpel till att matcha din lokala fil (kräver skriv+radera-rättighet)\">re📅",

		"cut_turbo": "yolo-knappen, du vill förmodligen INTE aktivera denna:$N$Nanvänd denna om du höll på att ladda upp en stor mängd filer och var tvungen att stänga webbläsaren, och du vill fortsätta uppladdningen så fort som möjligt$N$Ndetta ersätter hash-checken med en enkel <em>&quot;har denna fil samma filstorlek på servern?&quot;</em>, så om filinnehållet skiljer sig kommer den INTE att laddas upp$N$Ndu bör stänga av denna när uppladdningen är klar och sedan &quot;ladda upp&quot; samma filer igen för att låta klienten verifiera dem\">turbo",

		"cut_datechk": "har endast effekt med turbo-växeln påslagen$N$Nminskar yolo-faktorn lite grann; kollar om filtidsstämplarna på servern matchar dina$N$Ndetta <em>bör</em> fånga de flesta ofärdiga / korrumperade uppladdningarna, men kan inte ersätta ett fullständigt verifieringspass med turbo avstängt\">date-chk",

		"cut_u2sz": "storlek (i MiB) för varje uppladdnings-chunk; stora värden flyger bättre över atlanten. Prova lägre värden på mycket opålitliga uppkopplingar",

		"cut_flag": "garantera att endast en flik laddar upp samtidigt $N -- andra flikar måste också ha denna påslagen -- $N påverkar endast flikar på samma domän",

		"cut_az": "ladda upp filer i alfabetisk ordning, snarare än mindre filer först$N$Nalfabetisk ordning kan göra det enklare att se var något har gått fel, men uppladdningen blir lite långsammare över fiber / lokala nätverk",

		"cut_nag": "skicka en systemnotifikation när uppladdningar blir klara$N(endast om webbläsaren eller fliken inte är fokuserade)",
		"cut_sfx": "ljudnotifikation när uppladdningar blir klara$N(endast om webbläsaren eller fliken inte är fokuserade)",

		"cut_mt": "använd multitrådning för att accelerera filhashningen$N$Ndetta använder web-workers och kräver$Nmer RAM (upp till 512 MiB extra)$N$Nuppladdningar över https blir 30% snabbare, över http 4.5x snabbare\">mt",

		"cut_wasm": "använd wasm istället för webbläsarens inbyggda hashare; förbättrar hastigheten i chrome-baserade webbläsare men ökar CPU-lasten, och många äldre versioner av chrome har buggar som får webbläsaren att konsumera allt RAM-minne och krascha om detta är påslaget\">wasm",

		"cft_text": "favikon-text (låt stå tom och uppdatera sidan för att stänga av)",
		"cft_fg": "förgrundsfärg",
		"cft_bg": "bakgrundsfärg",

		"cdt_lim": "högsta antal filer att visa in en mapp",
		"cdt_ask": "när du når botten av vyn,$Nbe om en åtgärd istället för att ladda fler filer",
		"cdt_hsort": "hur många sorteringsregler (&lt;code&gt;,sorthref&lt;/code&gt;) att inkludera i media-URL:er. Sätts detta till 0 kommer regler i klickade medialänkar även att ignoreras",

		"tt_entree": "visa trädvy$NSnabbtangent: B",
		"tt_detree": "visa brödsmulor$NSnabbtangent: B",
		"tt_visdir": "skrolla till öppnad mapp",
		"tt_ftree": "växla mellan trädvy och textfiler$NHotkey: V",
		"tt_pdock": "visa överordnade mappar i en panel längst upp i vyn",
		"tt_dynt": "väx vyn när trädet expanderar",
		"tt_wrap": "automatisk radbrytning",
		"tt_hover": "visa överlånga rader när muspekaren hovrar över dem$N( skrollhjulet fungerar ej såvida inte pekaren$Nstår till vänster )",

		"ml_pmode": "vid mappens slut...",
		"ml_btns": "komm.",
		"ml_tcode": "konvertera",
		"ml_tcode2": "konvertera till",
		"ml_tint": "hy",
		"ml_eq": "ljudutjämnare",
		"ml_drc": "dynamikkompressor",

		"mt_loop": "upprepa en låt\">🔁",
		"mt_one": "stoppa uppspelningen efter en låt\">1️⃣",
		"mt_shuf": "blanda låtarna i varje mapp\">🔀",
		"mt_aplay": "spela automatiskt om det finns en låt-ID i länkar du har klickat på för att öppna sidan$N$Nom detta är avstängt kommer sidans adress inte att bli uppdaterad med en låt-ID om du spelar musik, för att förhindra automatisk uppspelning om dessa inställningar går förlorade men webbadressen återstår\">a▶",
		"mt_preload": "påbörja nedladdning av nästa låt i förväg för gapfri uppspelning\">ladda",
		"mt_prescan": "hoppa till nästa mapp i förväg så att webbläsaren$Nförblir glad och inte avbryter uppspelningen\">nav",
		"mt_fullpre": "försök att ladda ner hela låten i förväg;$N✅ aktivera på <b>opålitliga</b> uppkopplingar,$N❌ <b>avaktivera</b> kanske på långsamma uppkopplingar\">full",
		"mt_fau": "förhindra att uppspelningen avstannar på telefoner om nästa låt inte laddas tillräckligt snabbt i förväg (kan ge upphov till buggiga musiktaggar)\">☕️",
		"mt_waves": "vågformsreglage:$Nvisa ljudstyrkan i uppspelningsreglaget\">~s",
		"mt_npclip": "visa knappar för att kopiera låtinfo till urklippet\">/np",
		"mt_m3u_c": "visa knappar för att kopiera de valda$Nlåtarna som en m3u8-spellista\">📻",
		"mt_octl": "systemintegration (mediaknappar / skärmdisplay)\">os-ctl",
		"mt_oseek": "tillåt fram- och bakåtspolning via systemintegrationen$N$Nobs.: på vissa enheter (iPhone)$Nersätter detta knappen för nästa låt\">spola",
		"mt_oscv": "visa skivomslag i skärmdisplayen\">omslag",
		"mt_follow": "skrolla vyn till den spelande låten\">🎯",
		"mt_compact": "kompakt kontrollpanel\">⟎",
		"mt_uncache": "rensa cachen &nbsp;(prova detta om din webbläsare har cachat$Nen trasig kopia av en låt och den vägrar spela upp den)\">rensa",
		"mt_mloop": "upprepa den öppna mappen\">🔁 upprepa",
		"mt_mnext": "ladda nästa mapp och fortsätt\">📂 nästa",
		"mt_mstop": "stoppa uppspelningen\">⏸ stopp",
		"mt_cflac": "konvertera flac / wav till {0}\">flac",
		"mt_caac": "konvertera aac / m4a till {0}\">aac",
		"mt_coth": "konvertera allt annat (förutom mp3) till {0}\">annat",
		"mt_c2opus": "bäst val för pc, laptop, android\">opus",
		"mt_c2owa": "opus-weba, för iOS 17.5 och senare\">owa",
		"mt_c2caf": "opus-caf, för iOS 11 till 17\">caf",
		"mt_c2mp3": "använd detta på mycket gamla enheter\">mp3",
		"mt_c2flac": "bäst ljudkvalitet, men enorma nedladdningar\">flac",
		"mt_c2wav": "okomprimerad uppspelning (ännu större)\">wav",
		"mt_c2ok": "snyggt, bra val",
		"mt_c2nd": "det är inte det rekommenderade formatet för din enhet, men det är lungt",
		"mt_c2ng": "din enhet verkar inte stödja det här formatet, men vi provar ändå",
		"mt_xowa": "det finns buggar i iOS som hindrar uppspelning i bakgrunden med detta format; vänligen använd caf eller mp3 istället",
		"mt_tint": "nivå på bakgrundsfärg (0-100) på uppspelningsreglaget;$Ngör buffring mindre distraherande",
		"mt_eq": "aktiverar utjämning och förstärkning;$N$Nboost &lt;code&gt;0&lt;/code&gt; = standard 100%-volym (omodifierad)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = standard stereo (omodifierad)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% vänster-höger crossfeed$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = tar bort sång :^)$N$Nnär utjämningen är aktiverad blir gaplösa album verkligen gaplösa, så låt den stå påslagen med alla värden satta till 0 (förutom width = 1) om du bryr dig om det",
		"mt_drc": "aktiverar dynamikkompressorn (volymtillplattning / brickwaller); aktiverar även utjämnaren för att balansera röran, så sätt alla fält i utjämnaren förutom 'width' till 0 om du inte vill ha den$N$Nsänker all volym över THRESHOLD dB; för varje RATIO dB över THRESHOLD blir det 1 dB av output, så standardvärdena tresh = -24 och ratio = 12 innebär att volymen aldrig bör bli högre än -22 dB och det är säkert att höja utjämnarens boost till 0.8, eller t.o.m. 1.8 med ATK 0 och ett högt RLS-värde t.ex. 90 (fungerar endast i firefox; RLS är låst till högst 1 i andra webbläsare)$N$N(se wikipedia för en bättre förklaring)",

		"mb_play": "play",
		"mm_hashplay": "spela upp den här ljudfilen?",
		"mm_m3u": "tryck <code>Enter/OK</code> för att spela\ntryck <code>ESC/Avbryt</code> to Edit",
		"mp_breq": "firefox 82+ eller chrome 73+ eller iOS 15+ krävs",
		"mm_bload": "laddar...",
		"mm_bconv": "konverterar till {0}, vänligen vänta...",
		"mm_opusen": "din webbläsare kan inte spela upp aac- eller m4a-filer;\nkonvertering till opus är nu påslaget",
		"mm_playerr": "uppspelning misslyckades: ",
		"mm_eabrt": "Uppspelningen avbröts",
		"mm_enet": "Din uppkoppling är skum",
		"mm_edec": "Filen är korrumperad??",
		"mm_esupp": "Din webbläsare förstår inte detta format",
		"mm_eunk": "Okänt Fel",
		"mm_e404": "Kunde inte spela upp ljudfil; fel 404: Filen hittades inte.",
		"mm_e403": "Kunde inte spela upp ljudfil; fel 403: Åtkomst nekad.\n\nProva att ladda om sidan med F5, du kanske blev utloggad",
		"mm_e500": "Kunde inte spela upp ljudfil; fel 500: Kolla serverloggen.",
		"mm_e5xx": "Kunde inte spela upp ljudfil; serverfel ",
		"mm_nof": "hittade inga fler låtar i närheten",
		"mm_prescan": "Letar efter fler låtar...",
		"mm_scank": "Hittade nästa låt:",
		"mm_uncache": "cachen rensad; alla låtar kommer att laddas ner igen vid uppspelning",
		"mm_hnf": "den låten finns inte längre",

		"im_hnf": "den bilden finns inte längre",

		"f_empty": 'mappen är tom',
		"f_chide": 'detta kommer att dölja kolumnen «{0}»\n\ndu kan visa kolumner igen i inställningarna',
		"f_bigtxt": "den här filen är {0} MiB stor -- vill du verkligen visa den som text?",
		"f_bigtxt2": "visa endast slutet på filen? detta aktiverar även övervakning, vilket visar nya rader i filen i realtid",
		"fbd_more": '<div id="blazy"><code>{0}</code> av <code>{1}</code> filer visas; <a href="#" id="bd_more">visa {2}</a> eller <a href="#" id="bd_all">visa alla</a></div>',
		"fbd_all": '<div id="blazy"><code>{0}</code> av <code>{1}</code> filer visas; <a href="#" id="bd_all">visa alla</a></div>',
		"f_anota": "endast {0} av {1} objekt valdes;\nför att välja hela mappen, skrolla först till botten av vyn",

		"f_dls": 'fillänkarna i den öppna mappen har\nbytts till nedladdningslänkar',

		"f_partial": "För att säkert ladda ner en fil som för tillfället laddas upp, vänligen klicka på filen som har samma filnamn men utan <code>.PARTIAL</code>-filändelsen. Vänligen tryck Avbryt eller Escape för att göra detta.\n\nOm du bortser från denna varning och trycker OK eller Enter kommer den tillfälliga <code>.PARTIAL</code>-filen istället att laddas ner, vilket är nästan garanterat att ge dig korrumperad data.",

		"ft_paste": "klistra in {0} objekt$NSnabbtangent: ctrl-V",
		"fr_eperm": 'kan ej byta namn:\ndu har inte flytträttighet i denna mapp',
		"fd_eperm": 'kan ej radera:\ndu har inte raderingsrättighet i denna mapp',
		"fc_eperm": 'kan ej klippa:\ndu har inte flytträttighet i denna mapp',
		"fp_eperm": 'kan ej klistra in:\ndu har inte skrivrättighet i denna mapp',
		"fr_emore": "välj minst en fil att byta namn på",
		"fd_emore": "välj minst en fil att radera",
		"fc_emore": "välj minst en fil att klippa",
		"fcp_emore": "välj minst en fil att kopiera till urklippet",

		"fs_sc": "dela den öppna mappen",
		"fs_ss": "dela de urvalda filerna",
		"fs_just1d": "du kan inte välja mer än en mapp\neller blanda filer och mappar i samma urval",
		"fs_abrt": "❌ avbryt",
		"fs_rand": "🎲 slump.namn",
		"fs_go": "✅ skapa utdelning",
		"fs_name": "namn",
		"fs_src": "källa",
		"fs_pwd": "lösen",
		"fs_exp": "utgång",
		"fs_tmin": "min",
		"fs_thrs": "timmar",
		"fs_tdays": "dagar",
		"fs_never": "oändlig",
		"fs_pname": "valfritt länknamn; slumpas fram om detta står tomt",
		"fs_tsrc": "filen eller mappen att dela",
		"fs_ppwd": "valfritt lösenord",
		"fs_w8": "skapar utdelning...",
		"fs_ok": "tryck <code>Enter/OK</code> för att kopiera länken till urklipp\ntryck <code>ESC/Avbryt</code> för att stänga",

		"frt_dec": "kan laga vissa typer av trasiga filnamn\">avkoda-url",
		"frt_rst": "återställ modifierade filnamn till de ursprungliga\">↺ återställ",
		"frt_abrt": "avbryt och stäng denna panel\">❌ avbryt",
		"frb_apply": "BYT NAMN",
		"fr_adv": "batch-, metadata- och mönsteromskrivning\">avancerat",
		"fr_case": "skiftlägeskänsligt reguljärt uttryck\">skift",
		"fr_win": "windows-säkra namn; ersätt <code>&lt;&gt;:&quot;\\|?*</code> med japanska fullbreddtecken\">win",
		"fr_slash": "ersätt <code>/</code> med ett tecken som inte skapar nya mappar\">ingen /",
		"fr_re": "reguljärt sökuttryck att tillämpa på ursprungliga filnamn; grupper kan hänvisas till i formatfältet nedan via &lt;code&gt;(1)&lt;/code&gt; och &lt;code&gt;(2)&lt;/code&gt; osv.",
		"fr_fmt": "inspirerat av foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; ersätts av låttitel,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; skippar [detta] om artisten är tom$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; fyller i spårnumret till 2 siffror",
		"fr_pdel": "ta bort",
		"fr_pnew": "spara som",
		"fr_pname": "ge ett nytt namn på din inställning",
		"fr_aborted": "avbrutet",
		"fr_lold": "gammalt namn",
		"fr_lnew": "nytt namn",
		"fr_tags": "taggar för de valda filerna (skrivskyddat, endast som referens):",
		"fr_busy": "byter namn på {0} objekt...\n\n{1}",
		"fr_efail": "namnbyte misslyckades:\n",
		"fr_nchg": "{0} av de nya namnen ändrades p g a <code>win</code> och/eller <code>ingen /</code>\n\nÄr det okej att fortsätta med de nya namnen?",

		"fd_ok": "radering lyckades",
		"fd_err": "radering misslyckades:\n",
		"fd_none": "inget raderades; kanske blockerat av serverkonfigurationen (xbd)?",
		"fd_busy": "raderar {0} objekt...\n\n{1}",
		"fd_warn1": "RADERA dessa {0} objekt?",
		"fd_warn2": "<b>Sista chansen!</b> Det finns inget sätt att ångra detta. Radera?",

		"fc_ok": "klippte {0} objekt",
		"fc_warn": 'klippte {0} objekt, men:\n\nendast <b>denna</b> webbläsarflik kan klistra in dem\n(eftersom urvalet är så enormt stort)',

		"fcc_ok": "kopierade {0} objekt till urklippet",
		"fcc_warn": 'kopierade {0} objekt till urklippet, men:\n\nendast <b>denna</b> webbläsarflik kan klistra in dem\n(eftersom urvalet är så enormt stort)',

		"fp_apply": "använd dessa namn",
		"fp_ecut": "klipp eller kopiera filer / mappar först för att klistra / flytta dem\n\nobs.: du kan klippa och klistra mellan webbläsarflikar",
		"fp_ename": "{0} objekt kan ej flyttas hit eftersom filnamnen redan är tagna. Ge dem nya namn nedan för att fortsätta, eller lämna fältet tomt för att skippa:",
		"fcp_ename": "{0} objekt kan ej kopieras hit eftersom filnamnen redan är tagna. Ge dem nya namn nedan för att fortsätta, eller lämna fältet tomt för att skippa:",
		"fp_emore": "det finns fortfarande filnamnskrockar att fixa",
		"fp_ok": "flytt lyckades",
		"fcp_ok": "kopiering lyckades",
		"fp_busy": "flyttar {0} objekt...\n\n{1}",
		"fcp_busy": "kopierar {0} objekt...\n\n{1}",
		"fp_abrt": "avbryter...",
		"fp_err": "flytt misslyckades:\n",
		"fcp_err": "kopiering misslyckades:\n",
		"fp_confirm": "flytta dessa {0} objekt hit?",
		"fcp_confirm": "kopiera dessa {0} objekt hit?",
		"fp_etab": 'lyckades ej läsa urklippet från en annan webbläsarflik',
		"fp_name": "laddar upp en fil från din enhet. Ge den ett namn:",
		"fp_both_m": '<h6>välj vad som ska klistras in</h6><code>Enter</code> = Flytta {0} objekt från «{1}»\n<code>ESC</code> = Ladda upp {2} filer från din enhet',
		"fcp_both_m": '<h6>välj vad som ska klistras in</h6><code>Enter</code> = Kopiera {0} objekt från «{1}»\n<code>ESC</code> = Ladda upp {2} filer från din enhet',
		"fp_both_b": '<a href="#" id="modal-ok">Flytta</a><a href="#" id="modal-ng">Ladda upp</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopiera</a><a href="#" id="modal-ng">Ladda upp</a>',

		"mk_noname": "skriv ett namn i fältet till vänster först :p",

		"tv_load": "Laddar textfil:\n\n{0}\n\n{1}% ({2} av {3} MiB laddat)",
		"tv_xe1": "kunde ej ladda textfil:\n\nfel ",
		"tv_xe2": "404, filen hittades inte",
		"tv_lst": "lista av textfiler i",
		"tvt_close": "återvänd till mapp$NSnabbtangent: M (eller Esc)\">❌ stäng",
		"tvt_dl": "ladda ner denna fil$NSnabbtangent: Y\">💾 ladda ner",
		"tvt_prev": "visa föregående fil$NSnabbtangent: i\">⬆ föreg.",
		"tvt_next": "visa nästa fil$NSnabbtangent: K\">⬇ nästa",
		"tvt_sel": "välj fil &nbsp; ( för klipp / kopiera / radera / ... )$NSnabbtangent: S\">välj",
		"tvt_edit": "öppna fil i textredigerare$NSnabbtangent: E\">✏️ redigera",
		"tvt_tail": "övervaka filen; visa nya rader i realtid\">📡 övervaka",
		"tvt_wrap": "automatisk radbrytning\">↵",
		"tvt_atail": "lås vyn till sidans botten\">⚓",
		"tvt_ctail": "avkoda terminalfärger (ansi-escapesekvenser)\">🌈",
		"tvt_ntail": "gräns för scrollback (hur många byte ska behållas laddade)",

		"m3u_add1": "låt tillagd till m3u-spellista",
		"m3u_addn": "{0} låtar tillagda till m3u-spellista",
		"m3u_clip": "m3u-spellista kopierad till urklippet\n\ndu bör skapa en ny textfil som heter någonting.m3u och klistra in spellistan i det dokumentet; detta gör den uppspelbar",

		"gt_vau": "visa inte videor, spela endast ljudet\">🎧",
		"gt_msel": "urval av filer; ctrl-klicka en fil för standardbeteende$N$N&lt;em&gt;när detta är aktiverat: dubbelklicka en fil / mapp för att öppna den&lt;/em&gt;$N$NSnabbtangent: S\">urval",
		"gt_crop": "centrera och beskär miniatyrbilder\">beskär",
		"gt_3x": "högupplösta miniatyrbilder\">3x",
		"gt_zoom": "zoom",
		"gt_chop": "klipp",
		"gt_sort": "sortera efter",
		"gt_name": "namn",
		"gt_sz": "storlek",
		"gt_ts": "datum",
		"gt_ext": "typ",
		"gt_c1": "förkorta filnamn (visa mindre)",
		"gt_c2": "förläng filnamn (visa mer)",

		"sm_w8": "söker...",
		"sm_prev": "sökresultaten nedan är från en tidigare sökning:\n  ",
		"sl_close": "stäng sökresultaten",
		"sl_hits": "visar {0} träffar",
		"sl_moar": "ladda fler",

		"s_sz": "storlek",
		"s_dt": "datum",
		"s_rd": "sökväg",
		"s_fn": "namn",
		"s_ta": "taggar",
		"s_ua": "uppl.",
		"s_ad": "avanc.",
		"s_s1": "minimum MiB",
		"s_s2": "maximum MiB",
		"s_d1": "min. iso8601",
		"s_d2": "max. iso8601",
		"s_u1": "uppladdad efter",
		"s_u2": "och/eller före",
		"s_r1": "sökvägen innehåller &nbsp; (blankstegsseparerat)",
		"s_f1": "filnamnet innehåller &nbsp; (invertera med -intedetta)",
		"s_t1": "taggar innehåller &nbsp; (^=start, slut=$)",
		"s_a1": "specifika metadataegenskaper",

		"md_eshow": "kan ej visa ",
		"md_off": "[📜<em>läsmig</em>] avstängt i [⚙️] -- dokumentet är dolt",

		"badreply": "Kunde ej tolka svaret från servern",

		"xhr403": "403: Åtkomst nekad\n\nProva att ladda om sidan med F5, du kanske blev utloggad",
		"xhr0": "okänt (tappade förmodligen kontakt med servern, eller så är den nere)",
		"cf_ok": "ledsen -- DD" + wah + "oS-skyddet har aktiverats\n\nsaker bör fungera igen om 30 sekunder\n\nom inget händer, ladda om sidan med F5",
		"tl_xe1": "kunde inte visa undermappar:\n\nfel ",
		"tl_xe2": "404: Mappen hittades inte",
		"fl_xe1": "kunde inte visa filer i mapp:\n\nfel ",
		"fl_xe2": "404: Mappen hittades inte",
		"fd_xe1": "kunde inte skapa mapp:\n\nfel ",
		"fd_xe2": "404: Överordnad mapp hittades inte",
		"fsm_xe1": "kunde inte skicka meddelande:\n\ndel ",
		"fsm_xe2": "404: Överordnad mapp hittades inte",
		"fu_xe1": "kunde inte ladda unpost-listan från servern:\n\nfel ",
		"fu_xe2": "404: Filen hittades inte??",

		"fz_tar": "okomprimerad tar-fil i gnu-format (linux / mac)",
		"fz_pax": "okomprimerad tar-fil i pax-format (långsammare)",
		"fz_targz": "gnu-tar komprimerad med gzip-nivå 3$N$Ndetta är vanligtvis mycket långsamt,$Nanvänd okomprimerad tar istället",
		"fz_tarxz": "gnu-tar komprimerad med xz-nivå 1$N$Ndetta är vanligtvis mycket långsamt,$Nanvänd okomprimerad tar istället",
		"fz_zip8": "zip-fil med utf8-filnman (kan vara skum i windows 7 och äldre)",
		"fz_zipd": "zip-fil med standard cp437-filnamn, för riktigt gammal mjukvara",
		"fz_zipc": "cp437 med crc32 uträknad i förväg,$Nför MS-DOS PKZIP v2.04g (oktober 1993)$N(tar längre tid att behandla innan nedladdningen kan påbörjas)",

		"un_m1": "du kan radera dina senaste uppladdningar (eller avbryta pågående sådana) nedan",
		"un_upd": "uppdatera",
		"un_m4": "eller, dela filerna som syns nedan:",
		"un_ulist": "visa",
		"un_ucopy": "kopiera",
		"un_flt": "filter:&nbsp; sökvägen måste innehålla",
		"un_fclr": "rensa filtret",
		"un_derr": 'unpost-radering misslyckades:\n',
		"un_f5": 'något gick sönder, prova att uppdatera eller tryck på F5',
		"un_uf5": "ledsen men du måste uppdatera sidan (t.ex. genom att trycka på F5 eller CTRL-R) innan du kan avbryta den här uppladdningen",
		"un_nou": '<b>varning:</b> servern är för upptagen för att visa pågående uppladdningar; klicka på "uppdatera" om en stund',
		"un_noc": '<b>varning:</b> serverkonfigurationen tillåter inte unpost:ning av uppladdade filer',
		"un_max": "visar de första 2000 filerna (använd filtret)",
		"un_avail": "{0} av de senaste uppladdningarna kan raderas<br />{1} pågående uppladdningar kan avbrytas",
		"un_m2": "sorterat efter uppladdningstid; senast uppladdad först:",
		"un_no1": "tjosan! inga uppladdningar är tillräckligt nya",
		"un_no2": "tjosan! inga uppladdningar som matchar filtret är tillräckligt nya",
		"un_next": "radera de {0} nästkommande filerna",
		"un_abrt": "avbryt",
		"un_del": "radera",
		"un_m3": "laddar dina senaste uppladdningar...",
		"un_busy": "raderar {0} filer...",
		"un_clip": "{0} länkar kopierade till urklippet",

		"u_https1": "du bör",
		"u_https2": "byta till https",
		"u_https3": "för bättre prestanda",
		"u_ancient": 'din webbläsare är imponerande uråldrig -- du kanske borde <a href="#" onclick="goto(\'bup\')">använda bup istället</a>',
		"u_nowork": "firefox 53+ eller chrome 57+ eller iOS 11+ krävs",
		"tail_2old": "firefox 105+ eller chrome 71+ eller iOS 14.5+ krävs",
		"u_nodrop": 'din webbläsare är för gammal för dra-och-släpp-uppladdning',
		"u_notdir": "det där är ingen mapp!\n\ndin webbläsare är för gammal,\nprova dra-och-släpp istället",
		"u_uri": "släpp bilder från andra webbläsarfönster på den stora\nuppladdningsknappen för att ladda upp dem",
		"u_enpot": 'byt till <a href="#">potatisgränssnittet</a> (kan förbättra uppladdningshastigheten)',
		"u_depot": 'byt till <a href="#">det snygga gränssnittet</a> (kan försämra uppladdningshastigheten)',
		"u_gotpot": 'byter till potatisgränssnittet för förbättrad uppladdningshastighet,\n\nbyt gärna tillbaka om du vill!',
		"u_pott": "<p>filer: &nbsp; <b>{0}</b> färdiga, &nbsp; <b>{1}</b> misslyckade, &nbsp; <b>{2}</b> pågående, &nbsp; <b>{3}</b> köade</p>",
		"u_ever": "detta är den enkla uppladdaren; up2k kräver minst<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'detta är den enkla uppladdaren; <a href="#" id="u2yea">up2k</a> är bättre',
		"u_uput": 'optimera hastigheten (skippa checksumman)',
		"u_ewrite": 'du har inte skrivrättighet i denna mapp',
		"u_eread": 'du har inte läsrättighet i denna mapp',
		"u_enoi": 'serverkonfigurationen har inte slagit på sökning',
		"u_enoow": "du kan inte skriva över här; raderingsrättighet krävs",
		"u_badf": 'Dessa {0} filer (av totalt {1}) skippades, möjligtvis p.g.a. filsystemsrättigheter:\n\n',
		"u_blankf": 'Dessa {0} filer (av totalt {1}) är tomma; ladda upp dem ändå?\n\n',
		"u_applef": 'Dessa {0} filer (av totalt {1}) är förmodligen oönskade;\nTryck <code>OK/Enter</code> för att SKIPPA de följande filerna,\nTryck <code>Avbryt/ESC</code> för att INKLUDERA och LADDA UPP dem:\n\n',
		"u_just1": '\nDet kanske fungerar om du endast väljer en fil',
		"u_ff_many": "om du använder <b>Linux / MacOS / Android,</b> så <em>kan</em> denna mängd filer <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\">krascha Firefox!</a>\nom detta händer, vänligen försök igen (eller använd Chrome).",
		"u_up_life": "Denna uppladdning kommer att raderas från servern om\n{0} efter att den har blivit uppladdad",
		"u_asku": 'ladda upp dessa {0} filer till <code>{1}</code>',
		"u_unpt": "du kan ångra / radera denna uppladdning med 🧯 uppe till vänster",
		"u_bigtab": 'försöker att visa {0} filer\n\ndetta kan krascha din webbläsare, är du säker?',
		"u_scan": 'Scannar filer...',
		"u_dirstuck": 'katalogskannern fastnade när den försökte komma åt de följande {0} objekten; dessa kommer att skippas:',
		"u_etadone": 'Klar ({0}, {1} filer)',
		"u_etaprep": '(förbereder uppladdning)',
		"u_hashdone": 'hashning klar',
		"u_hashing": 'hashar',
		"u_hs": 'skakar hand...',
		"u_started": "filerna laddas nu upp; se [🚀]",
		"u_dupdefer": "duplikat; kommer att behandlas efter alla andra filer",
		"u_actx": "klicka här för att undvika prestandaförlust<br />när du byter till andra fönster/flikar",
		"u_fixed": "Okej!&nbsp; Fixat 👍",
		"u_cuerr": "misslyckades att ladda upp chunk {0} av {1};\nförmodligen harmlöst, fortsätter\n\nfil: {2}",
		"u_cuerr2": "servern avvisade uppladdningen (chunk {0} av {1});\nprovar igen senare\n\nfil: {2}\n\nfel ",
		"u_ehstmp": "provar igen; see nedåt till höger",
		"u_ehsfin": "servern avvisade förfrågan att färdigställa uppladdningen; provar igen...",
		"u_ehssrch": "servern avvisade förfrågan att söka; provar igen...",
		"u_ehsinit": "servern avvisade förfrågan att påbörja uppladdningen; provar igen...",
		"u_eneths": "nätverksfel vid handskakning; provar igen...",
		"u_enethd": "nätverksfel när destinationens existens testades; provar igen...",
		"u_cbusy": "väntar på att servern ska lita på oss igen efter nätverksfel...",
		"u_ehsdf": "servern fick slut på diskutrymme!\n\nprovar igen, ifall någon rensar upp\ntillräckligt med utrymme för att fortsätta",
		"u_emtleak1": "det verkar som att din webbläsare kanske har en minnesläcka;\nvänligen",
		"u_emtleak2": ' <a href="{0}">byt till https (rekommenderat)</a> eller ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'prova följande:\n<ul><li>tryck <code>F5</code> för att uppdatera sidan</li><li>avaktivera sedan &nbsp;<code>mt</code>&nbsp;-växeln i &nbsp;<code>⚙️-inställningarna</code></li><li>och prova att ladda upp igen</li></ul>Uppladdningar kommer att vara lite långsammare, men aja.\nBeklagar problemet!\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">har en buggfix</a> för detta',
		"u_emtleakf": 'prova följande:\n<ul><li>tryck <code>F5</code> för att uppdatera sidan</li><li>aktivera sedan <code>🥔</code> (potatis) i uppladdningsgränssnittet<li>och prova att ladda upp igen</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">kommer förhoppningsvis få en buggfix</a> vid något tillfälle',
		"u_s404": "hittades ej på servern",
		"u_expl": "förklara",
		"u_maxconn": "de flesta webbläsare begränsar detta till 6, men firefox låter dig höja gränsen med <code>connections-per-server</code> i <code>about:config</code>",
		"u_tu": '<p class="warn">VARNING: turbo är aktiverat, <span>&nbsp;det är möjligt att klienten inte upptäcker och återupptar ofärdiga uppladdningar; se tipset för turbo-växeln</span></p>',
		"u_ts": '<p class="warn">VARNING: turbo är aktiverat, <span>&nbsp;sökresultat kan vara felaktiga; se tipset för turbo-växeln</span></p>',
		"u_turbo_c": "serverkonfigurationen har avaktiverat turbo",
		"u_turbo_g": "avaktiverar turbo eftersom du inte har rättigheten\natt se mappars innehåll i den här volymen",
		"u_life_cfg": 'radera automatiskt efter <input id="lifem" p="60" /> min (eller <input id="lifeh" p="3600" /> timmar)',
		"u_life_est": 'uppladdningen kommer att raderas vid <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'denna mapp tvingar en\nhögsta livstid på {0}',
		"u_unp_ok": 'unpost är tillåten för {0}',
		"u_unp_ng": 'unpost är INTE tillåten',
		"ue_ro": 'du har endast läsrättighet till denna mapp\n\n',
		"ue_nl": 'du är inte inloggad',
		"ue_la": 'du är inloggad som "{0}"',
		"ue_sr": 'du är i filsökläge\n\nbyt till uppladdningsläge genom att klicka på förstoringsglaset 🔎 (bredvid den stora SÖK-knappen), och försök ladda upp igen\n\nledsen',
		"ue_ta": 'prova att ladda upp igen nu, det bör fungera',
		"ue_ab": "denna fil laddas redan upp till en annan mapp, och den uppladdningen måste färdigställas innan filen kan laddas upp någon annanstans.\n\nDu kan avbryta och glömma bort den uppladdningen med 🧯 uppe till vänster",
		"ur_1uo": "Okej: Filen laddades upp med framgång",
		"ur_auo": "Okej: Alla {0} filer laddades upp med framgång",
		"ur_1so": "Okej: Filen fanns på servern",
		"ur_aso": "Okej: Alla {0} filer fanns på servern",
		"ur_1un": "Uppladdningen misslyckades, ledsen",
		"ur_aun": "Alla {0} uppladdningar misslyckades, ledsen",
		"ur_1sn": "Filen hittades INTE på servern",
		"ur_asn": "De {0} filerna hittades INTE på servern",
		"ur_um": "Klar;\n{0} uppladdningar gick okej,\n{1} uppladdningar misslyckades, ledsen",
		"ur_sm": "Klar;\n{0} filer hittades på servern,\n{1} filer hittades INTE på servern",

		"lang_set": "uppdatera för att ändringen ska ta effekt?",
	},
	"tur": {
		"tt": "Türkçe",

		"cols": {
			"c": "işlem butonları",
			"dur": "süre",
			"q": "kalite / bitrate",
			"Ac": "ses kodlaması",
			"Vc": "video kodlaması",
			"Fmt": "format / yapı",
			"Ahash": "ses denetim toplamı",
			"Vhash": "video denetim toplamı",
			"Res": "çözünürlük",
			"T": "dosya türü",
			"aq": "ses kalitesi / bitrate",
			"vq": "video kalitesi / bitrate",
			"pixfmt": "subsampling / pixel yapısı",
			"resw": "yatay çözünürlük",
			"resh": "dikey çözünürlük",
			"chs": "ses kanalları",
			"hz": "örnekleme hızı"
		},

		"hks": [
			[
				"diğer",
				["ESC", "kapat"],

				"dosya yönetimi",
				["G", "liste / ızgara görünümü arasında geçiş yap"],
				["T", "küçük resimler / simgeler arasında geçiş yap"],
				["⇧ A/D", "küçük resim boyutu"],
				["ctrl-K", "seçileni sil"],
				["ctrl-X", "seçimi panoya kes"],
				["ctrl-C", "seçimi panoya kopyala"],
				["ctrl-V", "buraya yapıştır (taşı/kopyala)"],
				["Y", "seçileni indir"],
				["F2", "seçileni yeniden adlandır"],

				"dosya yönetimi seçimleri",
				["boşluk", "seçimi değiştir"],
				["↑/↓", "seçim imlecini hareket ettir"],
				["ctrl ↑/↓", "imleci ve görünümü hareket ettir"],
				["⇧ ↑/↓", "önceki/sonraki dosyayı seç"],
				["ctrl-A", "tüm dosyaları / klasörleri seç"],
			], [
				"navigasyon",
				["B", "içerik haritası / navigasyon paneli arasında geçiş yap"],
				["I/K", "önceki/sonraki klasör"],
				["M", "üst klasör (veya mevcut olanı daralt)"],
				["V", "navigasyon panelinde klasörler / metin dosyaları arasında geçiş yap"],
				["A/D", "navigasyon paneli boyutu"],
			], [
				"ses oynatıcı",
				["J/L", "önceki/sonraki şarkı"],
				["U/O", "10sn geri/ileri atla"],
				["0..9", "%0..%90 atla"],
				["P", "oynat/duraklat (aynı zamanda oynatıcıyı aç)"],
				["S", "şarkıyı seç"],
				["Y", "şarkıyı indir"],
			], [
				"resim görüntüleyici",
				["J/L, ←/→", "önceki/sonraki resim"],
				["Home/End", "ilk/son resim"],
				["F", "tam ekran"],
				["R", "sağa döndür"],
				["⇧ R", "sola döndür"],
				["S", "resmi seç"],
				["Y", "resmi indir"],
			], [
				"video oynatıcı",
				["U/O", "10sn geri/ileri atla"],
				["P/K/Space", "oynat/duraklat"],
				["C", "sıradakinden devam et"],
				["V", "döngü"],
				["M", "sessiz"],
				["[ ve ]", "döngü aralığını ayarla"],
			], [
				"metin dosyası görüntüleyici",
				["I/K", "önceki/sonraki dosya"],
				["M", "metin dosyasını kapat"],
				["E", "metin dosyasını düzenle"],
				["S", "dosyayı seç (kes/kopyala/yeniden adlandır)"],
			]
		],

		"m_ok": "Tamam",
		"m_ng": "İptal",

		"enable": "Etkinleştir",
		"danger": "TEHLİKE",
		"clipped": "panoya kopyalandı",

		"ht_s1": "saniye",
		"ht_s2": "saniye",
		"ht_m1": "dakika",
		"ht_m2": "dakika",
		"ht_h1": "saat",
		"ht_h2": "saat",
		"ht_d1": "gün",
		"ht_d2": "gün",
		"ht_and": " ve ",

		"goh": "kontrol paneli",
		"gop": 'önceki kardeş">önceki',
		"gou": 'üst klasör">üst',
		"gon": 'sonraki klasör">sonraki',
		"logout": "Çıkış ",
		"login": "Giriş",
		"access": " erişim",
		"ot_close": "alt menüyü kapat",
		"ot_search": "dosyaları özniteliklere, yol / ad, müzik etiketlerine veya bunların herhangi bir kombinasyonuna göre arayın$N$N&lt;code&gt;foo bar&lt;/code&gt; = hem «foo» hem de «bar» içermelidir,$N&lt;code&gt;foo -bar&lt;/code&gt; = «foo» içermeli ancak «bar» içermemelidir,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = «yana» ile başlamalı ve bir «opus» dosyası olmalıdır$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = tam olarak «try unite» içermelidir$N$N tarih formatı iso-8601'dir, gibi$N&lt;code&gt;2009-12-31&lt;/code&gt; veya &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: son yüklemelerinizi silin veya tamamlanmamış olanları iptal edin",
		"ot_bup": "bup: temel yükleyici, hatta netscape 4.0'ı destekler",
		"ot_mkdir": "mkdir: yeni bir dizin oluştur",
		"ot_md": "new-md: yeni bir markdown belgesi oluştur",
		"ot_msg": "msg: sunucu günlüğüne bir mesaj gönder",
		"ot_mp": "medya oynatıcı seçenekleri",
		"ot_cfg": "konfigürasyon seçenekleri",
		"ot_u2i": 'up2k: dosyaları yükle (yazma erişiminiz varsa) veya sunucuda bir yerde var olup olmadıklarını görmek için arama moduna geçiş yap$N$Nyüklemeler devam ettirilebilir, çok iş parçacıklı ve dosya zaman damgaları korunur, ancak [🎈]&nbsp; (temel yükleyici) ile karşılaştırıldığında daha fazla CPU kullanır<br /><br />yükleme sırasında, bu simge bir ilerleme göstergesi haline gelir!',
		"ot_u2w": 'up2k: devam desteği ile dosyaları yükle (tarayıcınızı kapatın ve daha sonra aynı dosyaları bırakın)$N$Nçok iş parçacıklı ve dosya zaman damgaları korunur, ancak [🎈]&nbsp; (temel yükleyici) ile karşılaştırıldığında daha fazla CPU kullanır<br /><br />yükleme sırasında, bu simge bir ilerleme göstergesi haline gelir!',
		"ot_noie": 'Lütfen Chrome / Firefox / Edge kullanın',

		"ab_mkdir": "dizin oluştur",
		"ab_mkdoc": "yeni markdown belgesi",
		"ab_msg": "sunucu günlüğüne mesaj gönder",

		"ay_path": "klasörlere atla",
		"ay_files": "dosyalara atla",

		"wt_ren": "seçilenleri yeniden adlandır$NKısa yol: F2",
		"wt_del": "Seçilen ögeleri sil$Kısa yol: ctrl-K",
		"wt_cut": "seçilen ögeleri kes &lt;small&gt;&lt;/small&gt;$NKısa yol: ctrl-X",
		"wt_cpy": "seçilen ögeleri panoya kopyala$N$NKısa yol: ctrl-C",
		"wt_pst": "daha önce kesilmiş / kopyalanmış bir seçimi yapıştır$NKısa yol: ctrl-V",
		"wt_selall": "tüm dosyaları seç$NKısa yol: ctrl-A (dosya odaklandığında)",
		"wt_selinv": "seçimi tersine çevir",
		"wt_zip1": "seçilenleri sıkıştırılmış bir arşiv olarak indir",
		"wt_selzip": "seçimi arşiv olarak indir",
		"wt_seldl": "seçimi ayrı dosyalar olarak indir$NHotkey: Y",
		"wt_npirc": "irc biçiminde parça bilgilerini kopyala",
		"wt_nptxt": "düz metin parça bilgilerini kopyala",
		"wt_m3ua": "m3u çalma listesine ekle (daha sonra <code>📻kopyala</code>ya tıklayın)",
		"wt_m3uc": "m3u çalma listesini panoya kopyala",
		"wt_grid": "ızgara / liste görünümünü değiştir$NHotkey: G",
		"wt_prev": "önceki parça$NHotkey: J",
		"wt_play": "oynat / duraklat$NHotkey: P",
		"wt_next": "sonraki parça$NHotkey: L",

		"ul_par": "paralel yüklemeler:",
		"ut_rand": "dosya adlarını rastgeleleştir",
		"ut_u2ts": "kendi dosyalarınızdan sunucuya$Nzaman damgasını kopyala\">📅",
		"ut_ow": "sunucudaki mevcut dosyaları üzerine yazmak mı?$N🛡️: asla (yerine yeni bir dosya adı oluşturur)$N🕒: sunucu dosyası sizinkinden daha eskiyse üzerine yaz$N♻️: dosyalar farklıysa her zaman üzerine yaz",
		"ut_mt": "yükleme yaparken diğer dosyaların hash'lenmesini durdur$N$kötü bir CPU veya HDD'ye sahipseniz kullanabilirsiniz.",
		"ut_ask": 'yüklemeye başlamadan önce doğrulama mesajı göster">💭',
		"ut_pot": "arayüzü daha az karmaşık hale getirerek$Nyükleme hızını yavaş cihazlarda artır",
		"ut_srch": "gerçekten yükleme yapma, bunun yerine dosyaların $N sunucuda var olup olmadığını kontrol et (okuma izniniz olan tüm klasörleri tarar)",
		"ut_par": "0'a ayarlayarak yüklemeleri durdur$N$Nbağlantınız yavaşsa değeri artırın$N$NLAN'daysanız veya sunucu HDD'si darboğaz yapıyorsa 1'de tutun",
		"ul_btn": "dosyaları / klasörleri <br>buraya sürükleyin (veya bana tıklayın)",
		"ul_btnu": "Y Ü K L E",
		"ul_btns": "A R A",

		"ul_hash": "hash",
		"ul_send": "gönder",
		"ul_done": "tamamlandı",
		"ul_idle1": "henüz bekleyen yükleme yok",
		"ut_etah": "ortalama &lt;em&gt;hash&lt;/em&gt; hızı ve bitişe kadar tahmini süre",
		"ut_etau": "ortalama &lt;em&gt;yükleme&lt;/em&gt; hızı ve bitişe kadar tahmini süre",
		"ut_etat": "ortalama &lt;em&gt;toplam&lt;/em&gt; hızı ve bitişe kadar tahmini süre",

		"uct_ok": "başarıyla tamamlandı",
		"uct_ng": "başarısız: başarısız / reddedildi / bulunamadı",
		"uct_done": "hem başarılı hem de başarısız",
		"uct_bz": "hash'liyor veya yüklüyor",
		"uct_q": "beklemede, gönderiliyor",

		"utl_name": "dosya adı",
		"utl_ulist": "liste",
		"utl_ucopy": "kopyala",
		"utl_links": "bağlantılar",
		"utl_stat": "durum",
		"utl_prog": "ilerleme",

		// kısa tutun:
		"utl_404": "404",
		"utl_err": "HATA",
		"utl_oserr": "OS-hatası",
		"utl_found": "bulundu",
		"utl_defer": "ertele",
		"utl_yolo": "YOLO",
		"utl_done": "tamamlandı",

		"ul_flagblk": "dosyalar sıraya alındı</b><br>ancak başka bir tarayıcı sekmesinde meşgul bir up2k var,<br>bu nedenle önce onun bitmesini bekliyor",
		"ul_btnlk": "sunucu yapılandırması bu anahtarı bu duruma kilitledi",

		"udt_up": "Yükle",
		"udt_srch": "Ara",
		"udt_drop": "buraya bırakın",

		"u_nav_m": '<h6>Pekâlâ, bakalım neyin  varmnış?</h6><code>Enter</code> = Dosyalar (bir veya birden fazla)\n<code>ESC</code> = Bir klasör (alt klasörler dahil)',
		"u_nav_b": '<a href="#" id="modal-ok">Dosyalar</a><a href="#" id="modal-ng">Tek klasör</a>',
		
		"cl_opts": "aç / kapat",
		"cl_themes": "tema",
		"cl_langs": "dil",
		"cl_ziptype": "klasör indirme",
		"cl_uopts": "up2k aç / kapat",
		"cl_favico": "favicon",
		"cl_bigdir": "big dirs",
		"cl_hsort": "#sort",
		"cl_keytype": "anahtar notasyonu",
		"cl_hiddenc": "gizli sütunlar",
		"cl_hidec": "gizle",
		"cl_reset": "sıfırla",
		"cl_hpick": "aşağıdaki tabloda gizlemek için sütun başlıklarına dokunun",
		"cl_hcancel": "sütun gizleme iptal edildi",

		"ct_grid": '田 ızgara',
		"ct_ttips": '◔ ◡ ◔">ℹ️ ipuçları',
		"ct_thumb": 'ızgara görünümünde, simgeler ve küçük resimler arasında geçiş yapın$NKısayol: T">🖼️ küçük resimler',
		"ct_csel": 'ızgara görünümünde dosya seçimi için CTRL ve SHIFT tuşlarını kullanın">seç',
		"ct_ihop": 'resim görüntüleyici kapatıldığında, en son görüntülenen dosyaya kaydırın">g⮯',
		"ct_dots": 'gizli dosyaları göster (sunucu izin veriyorsa)">nokta dosyaları',
		"ct_qdel": 'dosyaları silerken yalnız bir kez onay isteyin">qdel',
		"ct_dir1st": 'sıralamada klasörleri dosyalardan önceye koy">ilk 📁',
		"ct_nsort": 'doğal sıralama (başında sayı bulunan isimler için)">dsort',
		"ct_utc": 'tüm zaman damgalarını UTC diliminde göster">UTC',
		"ct_readme": 'README.md\'yi klasör listelemelerinde göster">📜 readme',
		"ct_idxh": 'index.html\'i klasör listelemeleri yerine göster">htm',
		"ct_sbars": 'kaydırma çubuklarını göster">⟊',

		"cut_umod": "eğer bir dosya sunucuda mevcutsa sunucudaki dosyanın son-değiştirilme zaman damgasını yereldekiyle değiştir (yazma+silme izinlerini gerektirir)\">re📅",

		"cut_turbo": "yolo butonu, bunu muhtemelen etkinleştirmek itemezsiniz:$N$Nyalnızca aynı anda çok fazla sayıda dosya yüklerken harhangi bir sebepten yüklemeyi durdurup anında yeniden başlatmanız gerekirse kullanın$N$Nbu, hash fonksiyonunu basit bir <em> ile değiştirir&quot;sunucudaki boyutu da aynı mı?&quot;</em> dosya içerikleri farklıysa yükleme devam ETMEYECEKTİR!$N$Nyükleme tamamlandığında bu ayarı kapatın ve sonra aynı dosyaları yeniden &quot;yüklemeyi&quot; deneyin ki sunucu bu dosyaları doğrulayabilsin\">turbo",

		"cut_datechk": "turbo modu açıksa hiçbir etkisi yoktur$N$Nyolo faktörünü az bir miktar düşürür; sunucudaki dosya zaman damgalarının sizinkiyle eşleşip eşleşmediğini kontrol eder$N$Nteorik olarak tamamlanmamış / bozuk yüklemelerin çoğunu yakalaması gerekir ancak turbo devre dışı bırakıldıktan sonra yapılan doğrulama geçişinin yerini tutamaz\">date-chk",

		"cut_u2sz": "her yükleme parçasının boyutu (MiB cinsinden); büyük değerler Atlantik boyunca daha iyi iletilir. Çok güvenilmez bağlantılarda düşük değerler deneyin",

		"cut_flag": "aynı anda sadece bir sekmenin yükleme yapabilmesini sağlayın $N -- diğer sekmelerde de bu ayar açık olmalıdır $N -- sadece aynı alan adı altındaki sekmeleri etkiler",

		"cut_az": "dosyaları en küçüğünden başlamak yerine alfabetik sırayla yükleyin$N$Nalefabetik sıralama, sunucuda bir şeylerin yanlış gidip gitmediğini gözlemlemenizi daha kolay hale getirebilir ancak fiber / LAN üzerinde yüklemeyi biraz yavaşlatır",

		"cut_nag": "yükleme tamamlandığında işletim sistemi bildirimi$N(sadece tarayıcı veya serkme aktif değilse)",
		"cut_sfx": "yükleme tamamlandığında sesli bildirim$N(sadece tarayıcı veya serkme aktif değilse)",

		"cut_mt": "dosya hash'lemesini hızlandırmak için çoklu izlekleri kullan$N$Nbu ayar web işlerini kullanır ve daha fazla$Nmore RAM (fazladan 512 MiB'a kadar) kullanır$N$https bağlantısını %30, http'yi ise 4.5 kat hızlandırır\">mt",

		"cut_wasm": "tarayıcının varsayılan hash fonksiyonu yerine WASM'ı kullan; Chrome tabanlı tarayıcılarda performansla birlikte CPU kullanımını artırır, ayrıca Chrome'un birçok eski sürümünde bu ayar etkinleştiğinde tarayıcının tüm RAM'i yemesine ve çökmesine sebep olan hatalar bulunur\">wasm",

		"cft_text": "favicon yazısı (devre dışı bırakmak için boş bırakıp yenileyin)",
		"cft_fg": "ön plan rengi",
		"cft_bg": "arka plan rengi",

		"cdt_lim": "bir klasörde gösterilecek maksimum dosya sayısı",
		"cdt_ask": "aşağı kaydırırken,$Ndaha fazla dosya yüklemek yerine,$Nne yapılacağını sor",
		"cdt_hsort": "medya-URL'lerinde dahil edilecek sıralama kurallarının sayısı (&lt;code&gt;,sorthref&lt;/code&gt;). Bunu 0 olarak ayarlamak, tıklanırken medya bağlantılarına dahil edilen sıralama kurallarını da yok sayacaktır",

		"tt_entree": "navigasyon panosunu göster (yan dizin panosu)$NHotkey: B",
		"tt_detree": "içerik haritasını göster$Kısayol: B",
		"tt_visdir": "seçili klasöre kaydır",
		"tt_ftree": "klasör ağacını / metin dosyalarını aç/kapat$Kısayol: V",
		"tt_pdock": "üstteki bir pencerede üst klasörleri göster",
		"tt_dynt": "ağaç genişledikçe otomatik büyüt",
		"tt_wrap": "kelime sarma",
		"tt_hover": "fare ile üzerine gelindiğinde taşan satırları göster$N( fare imleci sol kenarda değilse kaydırmayı bozar )",

		"ml_pmode": "klasör sonunda...",
		"ml_btns": "komutlar",
		"ml_tcode": "dönüştür",
		"ml_tcode2": "dönüştür",
		"ml_tint": "tonlama",
		"ml_eq": "ses eşitleyici",
		"ml_drc": "dinamik aralık sıkıştırıcı",

		"mt_loop": "bir şarkıyı döngüye al / tekrar et\">🔁",
		"mt_one": "bir şarkıdan sonra dur\">1️⃣",
		"mt_shuf": "klasörlerdeki şarkıları karıştır\">🔀",
		"mt_aplay": "sunucuya erişmek için kullandığın bağlantıda geçerli bir şarkı varsa otomatik oynat$N$Nbunu etkisiz kılmak aynı zamanda müzik oynatıldığında sayfa URL'nin değişmesini de engeller\">a▶",
		"mt_preload": "aralıksız oynatma için sıradaki şarkıyı önceden yüklemeye başla\">ön yükleme",
		"mt_prescan": "son şarkı bitmeden önce bir sonraki klasöre git$Nweb tarayıcısını mutlu tutar$Nbu nedenle oynatmayı durdurmaz\">nav",
		"mt_fullpre": "tüm şarkıyı ön yüklemeye çalış;$N✅ <b>güvenilmez</b> bağlantılarda etkinleştir,$N❌ <b>yavaş</b> bağlantılarda devre dışı bırak\">full",
		"mt_fau": "telefonlarda, bir sonraki şarkı yeterince hızlı ön yüklenmezse müziğin durmasını önle (etiketlerin bozuk görünmesine neden olabilir)\">☕️",
		"mt_waves": "dalga formu kaydırıcı:$Nses genliğini kaydırıcıda göster\">~s",
		"mt_npclip": "şu anda çalan şarkıyı kopyalamak için düğmeleri göster\">/np",
		"mt_m3u_c": "seçilen şarkıları m3u8 çalma listesi girişleri olarak kopyalamak için düğmeleri göster\">📻",
		"mt_octl": "os entegrasyonu (medya kısayolları / osd)\">os-ctl",
		"mt_oseek": "OS entegrasyonuyla şarkı ilerletmeye izin ver$N$Nnot: bazı cihazlarda (iPhone'lar)$Nbu, sıradaki şarkı düğmesini değiştirir\">ilerletme",
		"mt_oscv": "ekranda albüm kapaklarını göster\">görsel",
		"mt_follow": "oynatılan müzik ibaresini görünümde tut\">🎯",
		"mt_compact": "kompakt kontroller\">⟎",
		"mt_uncache": "önbelleği temizle &nbsp;(bunu, tarayıcınızın bozuk bir şarkı kopyasını önbelleğe alması nedeniyle çalmayı reddettiğinde deneyin)\">önbelleği temizle",
		"mt_mloop": "açık klasörü döngüye al\">🔁 döngü",
		"mt_mnext": "bir sonraki klasörü yükle ve devam et\">📂 sonraki",
		"mt_mstop": "oynatmayı durdur\">⏸ durdur",
		"mt_cflac": "flac / wav'ı {0}'a dönüştür\">flac",
		"mt_caac": "aac / m4a'yı {0}'a dönüştür\">aac",
		"mt_coth": "diğer tüm formatları (mp3 hariç) {0}'a dönüştür\">oth",
		"mt_c2opus": "masaüstü, dizüstü bilgisayarlar, android için en iyi seçim\">opus",
		"mt_c2owa": "opus-weba, iOS 17.5 ve üzeri için\">owa",
		"mt_c2caf": "opus-caf, iOS 11 ile 17 arasında için\">caf",
		"mt_c2mp3": "çok eski cihazlarda bunu kullanın\">mp3",
		"mt_c2flac": "en iyi ses kalitesi, ancak büyük indirmeler\">flac",
		"mt_c2wav": "sıkıştırılmamış oynatma (daha da büyük)\">wav",
		"mt_c2ok": "güzel, iyi seçim",
		"mt_c2nd": "bu, cihazınız için önerilen çıkış formatı değil, ama sorun değil",
		"mt_c2ng": "cihazınız bu çıkış formatını desteklemiyor gibi görünüyor, ama yine de deneyelim",
		"mt_xowa": "iOS'ta bu formatta arka plan oynatımını engelleyen hatalar var; lütfen bunun yerine caf veya mp3 kullanın",
		"mt_tint": "seekbar'da arka plan seviyesi (0-100)$ön belleğin daha az dikkat dağıtıcı olmasını sağlar",
		"mt_eq": "ekolayzer ve kazanç kontrolünü aktifleştirir;$N$Nboost &lt;code&gt;0&lt;/code&gt; = standart %100 ses (varsayılan)$N$Ngenişlik &lt;code&gt;1 &nbsp;&lt;/code&gt; = standart çift kanal (varsayılan)$Ngenişlik &lt;code&gt;0.5&lt;/code&gt; = %50 sol-sağ crossfeed$Ngenişlik &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nartış &lt;code&gt;-0.8&lt;/code&gt; &amp; artış &lt;code&gt;10&lt;/code&gt; = vokal kaldırma :^)$N$Nekolayzeri aktifleştirmek, aralıksız albümleri gerçekten aralıksız yapar, bu yüzden tüm değerleri 0'da bırakın (width = 1 hariç) tabii bunu umursuyorsnaız",
		"mt_drc": "dinamik aralık sıkıştırıcıyı (ses düzleştiriciyi) aktifleştirir; spagettiyi dengelemek için aynı zamanda EQ'yu da açar, bunun olmasını istemiyorsanız EQ'daki 'genişlik' hariç tüm alanları 0 yapın$N$Nsınır dB'inin üstündeki tüm sesleri kısar; sınırı geçen her 1 dB için ancak 1 dB ses verilir, yani varsayılan eşik -24 ve oran 12 değerleri sesin -22 dB'den yükseğe çıkmayacağını ve EQ artışının 0,8'e, hatta ATK 0 ve hayvan gibi RLS (örneğin 90, bu sadece Firefox'ta çalışır; diğer tarayıcılarda RLS en fazla 1'dir) gibi değerlerle 1.,8'e kadar güvenle çıkabileceğini gösteriyor$N$N(git vikipediye bak, orada daha iyi açıklanıyor)",

		"mb_play": "oynat",
		"mm_hashplay": "bu ses dosyası oynatılsın mı?",
		"mm_m3u": "Oynatmak için <code>Enter/Tamam</code> tuşuna basın\nDüzenlemek için <code>ESC/İptal</code> tuşuna basın",
		"mp_breq": "firefox 82+ veya chrome 73+ veya iOS 15+ gerektirir",
		"mm_bload": "şu anda yükleniyor...",
		"mm_bconv": "{0} formatına dönüştürülüyor, lütfen bekleyin...",
		"mm_opusen": "tarayıcınız aac / m4a dosyalarını oynatamıyor;\nopus'a dönüştürme etkinleştirildi",
		"mm_playerr": "oynatma hatası: ",
		"mm_eabrt": "Oynatma denemesi iptal edildi",
		"mm_enet": "İnternet bağlantınızda bir bokluk var",
		"mm_edec": "Bu dosya muhtemelen bozuk!",
		"mm_esupp": "Tarayıcınız salak, bu ses formatını anlamıyor",
		"mm_eunk": "Bilinmeyen Hata",
		"mm_e404": "Ses oynatılamadı; hata 404: Dosya bulunamadı.",
		"mm_e403": "Ses oynatılamadı; hata 403: Erişim reddedildi.\n\nYeniden yüklemek için F5 tuşuna basın, oturumunuz kapanmış olabilir.",
		"mm_e500": "Ses oynatılamadı; hata 500: Sunucu günlüklerini kontrol edin.",
		"mm_e5xx": "Ses oynatılamadı; sunucu hatası ",
		"mm_nof": "yakınlarda başka ses dosyası bulunamadı",
		"mm_prescan": "Sonraki şarkı aranıyor...",
		"mm_scank": "Sonraki şarkı bulundu:",
		"mm_uncache": "önbellek temizlendi; tüm şarkılar bir sonraki çalınmada yeniden indirilecek",
		"mm_hnf": "bu şarkı artık mevcut değil",

		"im_hnf": "bu resim artık mevcut değil",

		"f_empty": 'bu klasör boş',
		"f_chide": 'bu, «{0}» sütununu gizleyecektir\n\nsütunları ayarlar sekmesinden yeniden açabilirsiniz',
		"f_bigtxt": "bu dosya {0} MiB boyutunda -- Cidden saf yazı olarak mı görüntülemek istiyo'n?",
		"f_bigtxt2": "dosyanın sadece sonunu görüntülemek ister misin? bu, takip etme/sonlandırma işlemini de etkinleştirecek ve gerçek zamanlı olarak yeni eklenen metin satırlarını gösterecektir.",
		"fbd_more": '<div id="blazy"><code>{1}</code> dosyadan <code>{0}</code> tanesi gösteriliyor; <a href="#" id="bd_more">{2}</a> tanesini ya da <a href="#" id="bd_all">tümünü göster</a></div>',
		"fbd_all": '<div id="blazy"><code>{1}</code> dosyadan <code>{0}</code> tanesi gösteriliyor; <a href="#" id="bd_all">tümünü göster</a></div>',
		"f_anota": "{1} dosyadan sadece {0} tanesi seçildi;\nTüm klasörü seçmek için önce en alta kaydırın.",

		"f_dls": 'bu klasördeki dosya linkleri\nindirme linklerine dönüştürüldü',

		"f_partial": "Mevcutta yüklenen bir dosyayı güvenli bir şekilde indirmek için lütfen aynı adlı ama <code>.PARTIAL</code> uzantısına sahip olmayan dosyaya tıklayın. Lütfen bunu yapmak için İPTAL veya Esc tuşuna basın.\n\nTamam / Enter tuşuna basmak, bu uyarıyı yok sayacak ve bunun yerine <code>.PARTIAL</code> geçici dosyasını indirmeye devam edecektir ki bu da elinize bozuk veriler sunacaktır.",

		"ft_paste": "{0} ögeyi yapıştır$Kısayol: ctrl-V",
		"fr_eperm": 'yeniden adlandırılamıyor:\nbu klasörü “taşıma” izniniz yok',
		"fd_eperm": 'silinemiyor:\nbu klasörde “silme” izniniz yok',
		"fc_eperm": 'kesilemiyor:\nbu klasörde “taşıma“ izniniz yok',
		"fp_eperm": 'yapıştırılamıyor:\nbu klasörde “yazma“ izniniz yok',
		"fr_emore": "yeniden adlandırmak için en az bir öge seçin",
		"fd_emore": "silmek için en az bir öge seçin",
		"fc_emore": "kesmek için en az bir öge seçin",
		"fcp_emore": "panoya kopyalamak için en az bir öge seçin",

		"fs_sc": "bulunduğunuz klasörü paylaşın",
		"fs_ss": "seçilen dosyaları paylaşın",
		"fs_just1d": "birden fazla klasör seçemezsiniz\nveya bir seçimde dosyaları ve klasörleri karıştıramazsınız",
		"fs_abrt": "❌ iptal",
		"fs_rand": "🎲 rastgele.ad",
		"fs_go": "✅ paylaşımı oluştur",
		"fs_name": "isim",
		"fs_src": "kaynak",
		"fs_pwd": "şifre",
		"fs_exp": "son kullanma",
		"fs_tmin": "dakika",
		"fs_thrs": "saat",
		"fs_tdays": "gün",
		"fs_never": "sonsuz",
		"fs_pname": "isteğe bağlı bağlantı adı; boşsa rastgele olacaktır",
		"fs_tsrc": "paylaşılacak dosya veya klasör",
		"fs_ppwd": "isteğe bağlı şifre",
		"fs_w8": "paylaşım oluşturuluyor...",
		"fs_ok": "panoya kopyalamak için <code>Enter/Tamam</code> tuşuna basın\nkapatmak için <code>ESC/İptal</code> tuşuna basın",

		"frt_dec": "bazı bozuk dosya adlarını düzeltebilir\">url-decode",
		"frt_rst": "değiştirilen dosya adlarını orijinal haline döndür\">↺ sıfırla",
		"frt_abrt": "iptal et ve bu pencereyi kapat\">❌ iptal",
		"frb_apply": "YENİ ADI UYGULA",
		"fr_adv": "toplu / meta veri / desen yeniden adlandırma\">gelişmiş",
		"fr_case": "büyük/küçük harf duyarlı regex\">büyük/küçük harf",
		"fr_win": "windows'a uygun adlar; <code>&lt;&gt;:&quot;\\|?*</code> karakterlerini Japonca tam genişlik karakterleriyle değiştir\">win",
		"fr_slash": "<code>/</code> karakterini yeni klasörlerin oluşturulmasına neden olmayan bir karakterle değiştir\">/ yok",
		"fr_re": "orijinal dosya adlarına uygulanacak regex arama deseni; yakalama grupları aşağıdaki format alanında &lt;code&gt;(1)&lt;/code&gt; ve &lt;code&gt;(2)&lt;/code&gt; gibi belirtilebilir",
		"fr_fmt": "foobar2000'den esinlenilmiştir:$N&lt;code&gt;(title)&lt;/code&gt; şarkı başlığıyla değiştirilir,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; sanatçı boşsa [bu] kısmı atlar$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; parça numarasını 2 basamağa doldurur",
		"fr_pdel": "sil",
		"fr_pnew": "farklı kaydet",
		"fr_pname": "yeni ayarınızı adlandırın",
		"fr_aborted": "iptal edildi",
		"fr_lold": "eski ad",
		"fr_lnew": "yeni ad",
		"fr_tags": "seçilen dosyalar için etiketler (salt okunur, sadece referans için):",
		"fr_busy": "{0} öğe yeniden adlandırılıyor...\n\n{1}",
		"fr_efail": "yeniden adlandırma başarısız:\n",
		"fr_nchg": "{0} yeni adlardan bazıları <code>win</code> ve/veya <code>/ yok</code> nedeniyle değiştirildi\n\nBu değiştirilmiş yeni adlarla devam etmek için Tamam'a basın.",

		"fd_ok": "silme tamam",
		"fd_err": "silme başarısız:\n",
		"fd_none": "hiçbir şey silinmedi; belki sunucu yapılandırması (xbd) tarafından engellenmiştir?",
		"fd_busy": "{0} öğe siliniyor...\n\n{1}",
		"fd_warn1": "Bu {0} öge silinsin mi?",
		"fd_warn2": "<b>Son şans!</b> Geri alma imkanın yok. Silinsin mi?",

		"fc_ok": "{0} öge kesildi",
		"fc_warn": '{0} öge kesildi\n\namma velakin: sadece <b>bu</b> tarayıcı penceresine yapıştırılabilirler\n(çünkü seçiminin boyutu hayvan gibi)',

		"fcc_ok": "{0} öge panoya kopyalandı",
		"fcc_warn": '{0} öge panoya kopyalandı\n\namma velakin: sadece <b>bu</b> tarayıcı penceresine yapıştırılabilirler\n(çünkü seçiminin boyutu hayvan gibi)',

		"fp_apply": "bu adları kullan",
		"fp_ecut": "önce bazı dosyaları / klasörleri kes veya kopyala, sonra yapıştır / taşı\n\nnot: farklı tarayıcı sekmeleri arasında kes / yapıştır yapabilirsiniz",
		"fp_ename": "{0} öğe buraya taşınamaz çünkü adlar zaten alınmış. Devam etmek için aşağıda yeni adlar verin veya atlamak için adları boş bırakın:",
		"fcp_ename": "{0} öğe buraya kopyalanamaz çünkü adlar zaten alınmış. Devam etmek için aşağıda yeni adlar verin veya atlamak için adları boş bırakın:",
		"fp_emore": "hâlâ düzeltilmesi gereken bazı dosya adı çakışmaları var",
		"fp_ok": "taşıma tamam",
		"fcp_ok": "kopyalama tamam",
		"fp_busy": "{0} öğe taşınıyor...\n\n{1}",
		"fcp_busy": "{0} öğe kopyalanıyor...\n\n{1}",
		"fp_abrt": "İptal ediliyor...",
		"fp_err": "taşıma başarısız:\n",
		"fcp_err": "kopyalama başarısız:\n",
		"fp_confirm": "bu {0} öğeyi buraya taşımak istiyor musunuz?",
		"fcp_confirm": "bu {0} öğeyi buraya kopyalamak istiyor musunuz?",
		"fp_etab": 'diğer tarayıcı sekmesinden pano okunamadı',
		"fp_name": "cihazınızdan bir dosya yüklüyorsunuz. Bir ad verin:",
		"fp_both_m": '<h6>yapıştırılacak şeyi seçin</h6><code>Enter</code> = «{1}» içinden {0} dosyayı taşı\n<code>ESC</code> = cihazınızdan {2} dosyayı yükle',
		"fcp_both_m": '<h6>yapıştırılacak şeyi seçin</h6><code>Enter</code> = «{1}» içinden {0} dosyayı kopyala\n<code>ESC</code> = cihazınızdan {2} dosyayı yükle',
		"fp_both_b": '<a href="#" id="modal-ok">Taşı</a><a href="#" id="modal-ng">Yükle</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Kopyala</a><a href="#" id="modal-ng">Yükle</a>',

		"mk_noname": "bunu yapmadan önce soldaki boşluğa bir şeyler yazsana :p",

		"tv_load": "Metin belgesi yükleniyor:\n\n{0}\n\n{1}% ({2} of {3} MiB yüklendi)",
		"tv_xe1": "metin dosyası yüklenemedi:\n\nhata ",
		"tv_xe2": "404, dosya bulunamadı",
		"tv_lst": "metin dosyalarının listesi",
		"tvt_close": "klasör görünümüne dön$NKısayol: M (veya Esc)\">❌ kapat",
		"tvt_dl": "bu dosyayı indir$NKısayol: Y\">💾 indir",
		"tvt_prev": "önceki belgeyi göster$NKısayol: i\">⬆ önceki",
		"tvt_next": "sonraki belgeyi göster$NKısayol: K\">⬇ sonraki",
		"tvt_sel": "dosyayı seç$NKısayol: S\">seç",
		"tvt_edit": "dosyayı metin düzenleyicisinde aç$NKısayol: E\">✏️ düzenle",
		"tvt_tail": "dosyalardaki değişiklikleri izle; yeni satırları gerçek zamanlı göster\">📡 takip",
		"tvt_wrap": "kelime sarma\">↵",
		"tvt_atail": "sayfanın altına sabitle\">⚓",
		"tvt_ctail": "terminal renklerini çöz (ansi kaçış kodları)\">🌈",
		"tvt_ntail": "önbellek limiti (kaç byte yüklenmiş metin tutulacağı)",

		"m3u_add1": "şarkı m3u çalma listesine eklendi",
		"m3u_addn": "{0} şarkı m3u çalma listesine eklendi",
		"m3u_clip": "m3u çalma listesi şimdi panoya kopyalandı\n\nyeni bir metin dosyası oluşturmalı ve adını dosya.m3u koymalısınız ve çalma listesini o belgeye yapıştırmalısınız; bu sayede oynatılabilir hale gelecektir",

		"gt_vau": "videoları gösterme, sadece sesi oynat\">🎧",
		"gt_msel": "dosya seçimlerini etkinleştir; bir dosyayı geçersiz kılmak için ctrl-tıkla$N$N&lt;em&gt;etkin olduğunda: bir dosyayı / klasörü açmak için çift tıkla&lt;/em&gt;$N$NKısayol: S\">çoklu seçim",
		"gt_crop": "küçültülmüş önizlemeleri ortala\">kırp",
		"gt_3x": "yüksek çözünürlüklü önizlemeler\">3x",
		"gt_zoom": "yakınlaştır",
		"gt_chop": "kes",
		"gt_sort": "sırala",
		"gt_name": "isim",
		"gt_sz": "boyut",
		"gt_ts": "tarih",
		"gt_ext": "tip",
		"gt_c1": "dosya adlarını daha fazla kısalt (daha az göster)",
		"gt_c2": "dosya adlarını daha az kısalt (daha fazla göster)",

		"sm_w8": "aranıyor...",
		"sm_prev": "aşağıdaki arama sonuçları önceki bir sorgudan alınmıştır:\n  ",
		"sl_close": "arama sonuçlarını kapat",
		"sl_hits": "gösterilen {0} sonuç",
		"sl_moar": "daha fazla yükle",

		"s_sz": "boyut",
		"s_dt": "tarih",
		"s_rd": "yol",
		"s_fn": "isim",
		"s_ta": "etiketler",
		"s_ua": "yükleme@",
		"s_ad": "gel.",
		"s_s1": "en az MiB",
		"s_s2": "en fazla MiB",
		"s_d1": "en az iso8601",
		"s_d2": "en fazla. iso8601",
		"s_u1": "yüklendi",
		"s_u2": "veya önce",
		"s_r1": "dosya yolu &nbsp içerir; (boşlukla ayrılmış)",
		"s_f1": "isim &nbsp içerir; (-nope kullan)",
		"s_t1": "etiketler &nbsp içerir; (^=baş, son=$)",
		"s_a1": "özel metadata özellikleri",

		"md_eshow": "görüntülenemiyor:  ",
		"md_off": "[📜<em>beni-oku</em>], [⚙️] içinde kapalıdır -- belge gizli",

		"badreply": "Sunucudan gelen yanıt çözümlenemedi",

		"xhr403": "403: Erişim reddedildi\n\nF5'e basmayı deneyin, oturumunuz kapanmış olabilir",
		"xhr0": "bilinmiyor (muhtemelen sunucuya bağlantı kaybedildi veya sunucu çevrimdışı)",
		"cf_ok": "pardon yahu -- DD" + wah + "oS koruması şey etti\n\n30 saniyeye düzelmiş olurum\n\nbi' halt olmazsa f5'e basarak sayfayı yenile",
		"tl_xe1": "alt klasörler listelenemiyor:\n\nhata ",
		"tl_xe2": "404: klasör bulunamadı",
		"fl_xe1": "dosyalar listelenemiyor:\n\nhata ",
		"fl_xe2": "404: klasör bulunamadı",
		"fd_xe1": "alt klasör oluşturulamadı:\n\nhata ",
		"fd_xe2": "404: Üst klasör bulunamadı",
		"fsm_xe1": "mesaj gönderilemedi:\n\nhata ",
		"fsm_xe2": "404: Üst klasör bulunamadı",
		"fu_xe1": "sunucudan unpost(?) listesini yüklemek başarısız oldu:\n\nhata ",
		"fu_xe2": "404: Dosya bulunamadı!!",

		"fz_tar": "sıkıştırılmamış gnu-tar dosyası (linux / mac)",
		"fz_pax": "sıkıştırılmamış pax-format tar (daha yavaş)",
		"fz_targz": "gnu-tar ile gzip seviye 3 sıkıştırma$N$Nbu genellikle çok yavaştır, bu yüzden$Nsıkıştırılmamış tar kullanın",
		"fz_tarxz": "gnu-tar ile xz seviye 1 sıkıştırma$N$Nbu genellikle çok yavaştır, bu yüzden$Nsıkıştırılmamış tar kullanın",
		"fz_zip8": "utf8 dosya adları ile zip (windows 7 ve daha eski sürümlerde sorunlu olabilir)",
		"fz_zipd": "gerçekten eski yazılımlar için geleneksel cp437 dosya adları ile zip",
		"fz_zipc": "erken hesaplanan crc32 ile cp437,$NMS-DOS PKZIP v2.04g (ekim 1993) için$N(indirmenin başlamasından önce işlenmesi daha uzun sürer)",

		"un_m1": "aşağıdan son yüklemelerinizi (veya tamamlanmamış olanları) silebilirsiniz",
		"un_upd": "yenile",
		"un_m4": "veya aşağıda görünen dosyaları paylaşın:",
		"un_ulist": "göster",
		"un_ucopy": "kopyala",
		"un_flt": "isteğe bağlı filtre:&nbsp; URL şunu içermelidir:",
		"un_fclr": "filtreyi temizle",
		"un_derr": 'unpost-delete failed:\n',
		"un_f5": 'bir şeyler bozuldu, lütfen yenilemeyi deneyin veya F5 tuşuna basın',
		"un_uf5": "üzgünüm ama bu yükleme iptal edilmeden önce sayfayı yenilemeniz gerekiyor (F5 veya CTRL-R tuşlarına basarak)",
		"un_nou": '<b>uyarı:</b> sunucu tamamlanmamış yüklemeleri göstermek için çok meşgul; birazdan "yenile" bağlantısına tıklayın',
		"un_noc": '<b>uyarı:</b> tamamen yüklenmiş dosyaların unpost edilmesi sunucu yapılandırmasında etkinleştirilmemiştir/izin verilmemiştir',
		"un_max": "ilk 2000 dosya gösteriliyor (filtreyi kullan)",
		"un_avail": "son yüklemelerin {0} tanesi silinebilir<br />tamamlanmayanların {1} tanesi iptal edilebilir",
		"un_m2": "yükleme zamanına göre sıralandı; en son önce:",
		"un_no1": "Hayda! yeterince güncel yükleme yok",
		"un_no2": "Hayda! o filtreye uyan yeterince güncel yükleme yok",
		"un_next": "aşağıdaki {0} dosyayı sil",
		"un_abrt": "iptal",
		"un_del": "sil",
		"un_m3": "son yüklemelerinizi hazırlanıyor...",
		"un_busy": "{0} dosya siliniyor...",
		"un_clip": "{0} bağlantı panoya kopyalandı",

		"u_https1": "daha iyi performans",
		"u_https2": "için https'i",
		"u_https3": "kullanın",
		"u_ancient": 'tarayıcınız resmen fosilleşmiş -- belki de <a href="#" onclick="goto(\'bup\')">bup kullanmalısınız</a>',
		"u_nowork": "firefox 53+ veya chrome 57+ veya iOS 11+ gerekiyor",
		"tail_2old": "firefox 105+ veya chrome 71+ veya iOS 14.5+ gerekiyor",
		"u_nodrop": 'tarayıcınız sürükleyip bırakmak için çok eski',
		"u_notdir": "bu bir klasör değil!\n\ntarayıcınız çok eski,\nlütfen bunun yerine sürükleyip bırakmayı deneyin",
		"u_uri": "başka tarayıcı pencerelerinden sürükle-bırak ile yükleme yapmak için,\nlütfen büyük yükleme düğmesinin üstüne bırakın",
		"u_enpot": '<a href="#">Patates arayüze</a> geçiş yap (yükleme hızını artırabilir)',
		"u_depot": '<a href="#">Havalı arayüze</a> geçiş yap (yükleme hızını azaltabilir)',
		"u_gotpot": 'yükleme hızını artırmak için patates arayüzüne geçiliyor,\n\nkatılmıyorsanız geri dönmekte özgürsünüz!',
		"u_pott": "<p>dosyalar: &nbsp; <b>{0}</b> tamamlandı, &nbsp; <b>{1}</b> başarısız, &nbsp; <b>{2}</b> meşgul, &nbsp; <b>{3}</b> sırada bekliyor</p>",
		"u_ever": "bu temel yükleyici; up2k en az<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1 gerektirir",
		"u_su2k": 'bu temel yükleyici; <a href="#" id="u2yea">up2k</a> daha iyidir',
		"u_uput": 'hız için optimize et (kontrol toplamını atla)',
		"u_ewrite": 'bu klasöre yazma izniniz yok',
		"u_eread": 'bu klasörü okuma izniniz yok',
		"u_enoi": 'dosya arama sunucu yapılandırmasında etkin değil',
		"u_enoow": "üstüne yazma burada çalışmayacak; Silme izni gerekiyor",
		"u_badf": 'Bu {0} dosya (toplam {1} arasında) atlandı, muhtemelen dosya sistemi izinleri nedeniyle:\n\n',
		"u_blankf": 'Bu {0} dosya (toplam {1} arasında) boş / boş; yine de yüklemek ister misiniz?\n\n',
		"u_applef": 'Bu {0} dosya (toplam {1} arasında) muhtemelen istenmiyor;\nAşağıdaki dosyaları ATLAMAK için <code>TAMAM/Enter</code> tuşuna basın,\nyüklemek için <code>İptal/ESC</code> tuşuna basın\n\n',
		"u_just1": '\nBelki sadece bir dosya seçerseniz daha iyi çalışır',
		"u_ff_many": "eğer <b>Linux / MacOS / Android</b> kullanıyorsanız bu kadar çok dosya yüklemenin <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>Firefox'u</em> çökertme ihtimali var!</a>\nEğer çökerse lütfen tekrar deneyin (veya Chrome kullanın).",
		"u_up_life": "Bu yükleme, tamamlandıktan {0} süre sonra sunucudan silinecek\n",
		"u_asku": 'bu {0} dosya <code>{1}</code> içerisine yükleniyor',
		"u_unpt": "bu yüklemeyi sol üstteki 🧯 ile geri alabilir / silebilirsiniz",
		"u_bigtab": '{0} dosya görüntülenmek üzere\n\nBu kadar fazlası tarayıcınızı çökertebilir, emin misiniz?',
		"u_scan": 'Dsyalar tarıyor...',
		"u_dirstuck": 'dizin yineleyicisi aşağıdaki {0} öğeye erişmeye çalışırken takıldı; atlanacak:',
		"u_etadone": 'Tamamlandı ({0}, {1} dosya)',
		"u_etaprep": '(yüklemeye hazırlanıyor)',
		"u_hashdone": 'hash\'leme tamamlandı',
		"u_hashing": 'hash\'leniyor',
		"u_hs": 'el sıkılıyor...',
		"u_started": "dosyalar şu anda yükleniyor; [🚀]'i gör",
		"u_dupdefer": "başka bir dosyanın kopyası; diğer tüm dosyalardan sonra işlenecek",
		"u_actx": "diğer pencereler/sekmeler arasında geçiş yaparken <br /> performansın düşmemesi için bu yazıya tıklayın",
		"u_fixed": "Timam!&nbsp; Hallettim 👍",
		"u_cuerr": "parça {0} / {1} yüklenemedi;\nmuhtemelen zararsız, devam ediliyor\n\ndosya: {2}",
		"u_cuerr2": "sunucu yüklemeyi reddetti (parça {0} / {1});\nsonra tekrar denenecek\n\ndosya: {2}\n\nhata ",
		"u_ehstmp": "tekrar denenecek; sağ alt köşeye mak",
		"u_ehsfin": "sunucu yüklemeyi tamamlama isteğini reddetti; tekrar deniyor...",
		"u_ehssrch": "sunucu arama yapma isteğini reddetti; tekrar deniyor...",
		"u_ehsinit": "sunucu yüklemeyi başlatma isteğini reddetti; tekrar deniyor...",
		"u_eneths": "yükleme el sıkışması sırasında ağ hatası; tekrar deniyor...",
		"u_enethd": "hedef varlığını test ederken ağ hatası; tekrar deniyor...",
		"u_cbusy": "ağ kesintisinden sonra sunucunun bize tekrar güvenmesini bekliyoruz...",
		"u_ehsdf": "sunucuda disk alanı kalmadı!\n\ndevam edebilmek için birinin\nyeterli alan açmasını bekleyeceğiz",
		"u_emtleak1": "görünüşe göre web tarayıcınızda bir bellek sızıntısı var;\nlütfen",
		"u_emtleak2": ' <a href="{0}">https\'ye geçin (önerilir)</a> veya ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'sırayla şunları deneyin:\n<ul><li>sayfayı yenilemek için <code>F5</code>\'e basın</li><li>sonra &nbsp;<code>mt</code>&nbsp; düğmesini &nbsp;<code>⚙️ ayarlar</code> menüsünde devre dışı bırakın</li><li>ve o yüklemeyi tekrar deneyin</li></ul>Yüklemeler biraz daha yavaş olacaktır, ama salla gitsin.\nSorun için özür dileriz!\n\nDipnot: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">için bir hata düzeltmesi</a>',
		"u_emtleakf": 'şunları deneyin:\n<ul><li>sayfayı yenilemek için <code>F5</code>\'e basın</li><li>sonra yükleme arayüzünde <code>🥔</code> (patates) seçeneğini etkinleştirin<li>ve yüklemeyi tekrar deneyin</li></ul>\nDipnot: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">için muhtemel bir hata düzeltmesi</a>',
		"u_s404": "sunucuda bulunamadı",
		"u_expl": "açıklama",
		"u_maxconn": "çoğu tarayıcı bunu 6 ile sınırlar, ancak firefox bunu <code>about:config</code> içinde <code>connections-per-server</code> ile artırmanıza izin verir",
		"u_tu": '<p class="warn">UYARI: turbo etkin, <span>&nbsp;istemci tamamlanmamış yüklemeleri algılayamayabilir ve devam ettiremeyebilir; turbo düğmesinden ipuçlarına bakabilirsiniz</span></p>',
		"u_ts": '<p class="warn">UYARI: turbo etkin, <span>&nbsp;arama sonuçları yanlış olabilir; turbo düğmesi ipuçlarına bakın</span></p>',
		"u_turbo_c": "turbo sunucu yapılandırmasında devre dışı bırakıldı",
		"u_turbo_g": "turbo devre dışı bırakılıyor çünkü bu alanda\ndizin listeleme ayrıcalıklarınız yok",
		"u_life_cfg": 'yüklemeleri <input id="lifem" p="60" /> dk (veya <input id="lifeh" p="3600" /> saat) sonra otomatik olarak sil',
		"u_life_est": 'yükleme <span id="lifew" tt="local time">---</span> sonra silinecek',
		"u_life_max": 'bu klasör bir\nmaksimum ömür {0} uygular',
		"u_unp_ok": 'unpost {0} için izin verildi',
		"u_unp_ng": 'unpost izin verilmeyecek',
		"ue_ro": 'bu klasöre erişiminiz Salt Okuma\n\n',
		"ue_nl": 'şu anda oturum açmamışsınız',
		"ue_la": 'şu anda "{0}" olarak oturum açmışsınız',
		"ue_sr": 'şu anda dosya arama modundasınız\n\nbüyüteç simgesine tıklayarak yükleme moduna geçin 🔎 (büyük ARAMA düğmesinin yanındaki) ve tekrar yüklemeyi deneyin\n\nyeter be',
		"ue_ta": 'tekrar yüklemeyi deneyin, artık çalışsana be',
		"ue_ab": "bu dosya zaten başka bir klasöre yükleniyor ve o yükleme tamamlanmadan dosya başka bir yere yüklenemez.\n\nİlk yüklemeyi iptal edip unutmak için sol üstteki 🧯 simgesini kullanabilirsiniz.",
		"ur_1uo": "OK: Dosya başarıyla yüklendi",
		"ur_auo": "OK: {0} dosyanın tamamı başarıyla yüklendi",
		"ur_1so": "OK: Dosya sunucuda bulundu",
		"ur_aso": "OK: {0} dosyanın tamamı sunucuda bulundu",
		"ur_1un": "Yükleme başarısız oldu, üzgünüm",
		"ur_aun": "{0} yüklemenin tamamı başarısız oldu, üzgünüm",
		"ur_1sn": "Dosya sunucuda bulunamadı",
		"ur_asn": "{0} dosyas sunucuda bulunamadı",
		"ur_um": "Tamamlandı;\n{0} yükleme başarılı,\n{1} yükleme başarısız oldu, üzgünüm",
		"ur_sm": "Tamamlandı;\n{0} dosya sunucuda bulundu,\n{1} dosya sunucuda bulunamadı",

		"lang_set": "Değişikliklerin etki göstermesi için sayfa yenilensin mi?",
	},
	"ukr": {
		"tt": "Українська",

		"cols": {
			"c": "кнопки дій",
			"dur": "тривалість",
			"q": "якість / бітрейт",
			"Ac": "аудіо кодек",
			"Vc": "відео кодек",
			"Fmt": "формат / контейнер",
			"Ahash": "контрольна сума аудіо",
			"Vhash": "контрольна сума відео",
			"Res": "роздільність",
			"T": "тип файлу",
			"aq": "якість аудіо / бітрейт",
			"vq": "якість відео / бітрейт",
			"pixfmt": "підвибірка / структура пікселів",
			"resw": "горизонтальна роздільність",
			"resh": "вертикальна роздільність",
			"chs": "аудіо канали",
			"hz": "частота дискретизації"
		},

		"hks": [
			[
				"різне",
				["ESC", "закрити різні речі"],

				"файловий менеджер",
				["G", "перемкнути список / сітку"],
				["T", "перемкнути мініатюри / іконки"],
				["⇧ A/D", "розмір мініатюр"],
				["ctrl-K", "видалити вибране"],
				["ctrl-X", "вирізати до буфера"],
				["ctrl-C", "копіювати до буфера"],
				["ctrl-V", "вставити (перемістити/копіювати) сюди"],
				["Y", "завантажити вибране"],
				["F2", "перейменувати вибране"],

				"вибір файлів у списку",
				["space", "перемкнути вибір файлу"],
				["↑/↓", "перемістити курсор вибору"],
				["ctrl ↑/↓", "перемістити курсор і вікно"],
				["⇧ ↑/↓", "вибрати попередній/наступний файл"],
				["ctrl-A", "вибрати всі файли / папки"],
			], [
				"навігація",
				["B", "перемкнути хлібні крихти / панель навігації"],
				["I/K", "попередня/наступна папка"],
				["M", "батьківська папка (або згорнути поточну)"],
				["V", "перемкнути папки / текстові файли в панелі навігації"],
				["A/D", "розмір панелі навігації"],
			], [
				"аудіо плеєр",
				["J/L", "попередня/наступна пісня"],
				["U/O", "перемотати на 10сек назад/вперед"],
				["0..9", "перейти до 0%..90%"],
				["P", "відтворити/пауза (також запускає)"],
				["S", "вибрати поточну пісню"],
				["Y", "завантажити пісню"],
			], [
				"переглядач зображень",
				["J/L, ←/→", "попереднє/наступне зображення"],
				["Home/End", "перше/останнє зображення"],
				["F", "повний екран"],
				["R", "повернути за годинниковою стрілкою"],
				["⇧ R", "повернути проти годинникової стрілки"],
				["S", "вибрати зображення"],
				["Y", "завантажити зображення"],
			], [
				"відео плеєр",
				["U/O", "перемотати на 10сек назад/вперед"],
				["P/K/Space", "відтворити/пауза"],
				["C", "продовжити відтворення наступного"],
				["V", "повтор"],
				["M", "вимкнути звук"],
				["[ and ]", "встановити інтервал повтору"],
			], [
				"переглядач текстових файлів",
				["I/K", "попередній/наступний файл"],
				["M", "закрити текстовий файл"],
				["E", "редагувати текстовий файл"],
				["S", "вибрати файл (для вирізання/копіювання/перейменування)"],
			]
		],

		"m_ok": "Гаразд",
		"m_ng": "Скасувати",

		"enable": "Увімкнути",
		"danger": "НЕБЕЗПЕКА",
		"clipped": "скопійовано до буфера обміну",

		"ht_s1": "секунда",
		"ht_s2": "секунд",
		"ht_m1": "хвилина",
		"ht_m2": "хвилин",
		"ht_h1": "година",
		"ht_h2": "годин",
		"ht_d1": "день",
		"ht_d2": "днів",
		"ht_and": " і ",

		"goh": "панель керування",
		"gop": 'попередній сусід">назад',
		"gou": 'батьківська папка">вгору',
		"gon": 'наступна папка">далі',
		"logout": "Вийти ",
		"login": "увійти", //m
		"access": " доступ",
		"ot_close": "закрити підменю",
		"ot_search": "пошук файлів за атрибутами, шляхом / іменем, музичними тегами, або будь-якою комбінацією$N$N&lt;code&gt;foo bar&lt;/code&gt; = має містити «foo» і «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = має містити «foo», але не «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = починатися з «yana» і бути файлом «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = містити точно «try unite»$N$Nформат дати - iso-8601, наприклад$N&lt;code&gt;2009-12-31&lt;/code&gt; або &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "скасувати: видалити недавні завантаження або перервати незавершені",
		"ot_bup": "bup: основний завантажувач, підтримує навіть netscape 4.0",
		"ot_mkdir": "mkdir: створити нову папку",
		"ot_md": "new-md: створити новий markdown документ",
		"ot_msg": "msg: надіслати повідомлення в лог сервера",
		"ot_mp": "налаштування медіаплеєра",
		"ot_cfg": "параметри конфігурації",
		"ot_u2i": 'up2k: завантажити файли (якщо у вас є доступ для запису) або переключитися на режим пошуку, щоб побачити, чи існують вони десь на сервері$N$Nзавантаження можна поновлювати, багатопотокові, і часові мітки файлів зберігаються, але використовує більше CPU ніж [🎈]&nbsp; (основний завантажувач)<br /><br />під час завантаження ця іконка стає індикатором прогресу!',
		"ot_u2w": 'up2k: завантажити файли з підтримкою поновлення (закрийте браузер і перетягніть ті самі файли пізніше)$N$Nбагатопотокові, і часові мітки файлів зберігаються, але використовує більше CPU ніж [🎈]&nbsp; (основний завантажувач)<br /><br />під час завантаження ця іконка стає індикатором прогресу!',
		"ot_noie": 'Будь ласка, використовуйте Chrome / Firefox / Edge',

		"ab_mkdir": "створити папку",
		"ab_mkdoc": "новий markdown документ",
		"ab_msg": "надіслати повідомлення в лог сервера",

		"ay_path": "перейти до папок",
		"ay_files": "перейти до файлів",

		"wt_ren": "перейменувати вибрані елементи$NГаряча клавіша: F2",
		"wt_del": "видалити вибрані елементи$NГаряча клавіша: ctrl-K",
		"wt_cut": "вирізати вибрані елементи &lt;small&gt;(потім вставити в іншому місці)&lt;/small&gt;$NГаряча клавіша: ctrl-X",
		"wt_cpy": "копіювати вибрані елементи до буфера$N(щоб вставити їх в іншому місці)$NГаряча клавіша: ctrl-C",
		"wt_pst": "вставити раніше вирізане / скопійоване$NГаряча клавіша: ctrl-V",
		"wt_selall": "вибрати всі файли$NГаряча клавіша: ctrl-A (коли фокус на файлі)",
		"wt_selinv": "інвертувати вибір",
		"wt_zip1": "завантажити цю папку як архів",
		"wt_selzip": "завантажити вибір як архів",
		"wt_seldl": "завантажити вибір як окремі файли$NГаряча клавіша: Y",
		"wt_npirc": "копіювати інформацію треку у форматі irc",
		"wt_nptxt": "копіювати інформацію треку у текстовому форматі",
		"wt_m3ua": "додати до m3u плейлисту (потім клацніть <code>📻копіювати</code>)",
		"wt_m3uc": "копіювати m3u плейлист до буфера",
		"wt_grid": "перемкнути сітку / список$NГаряча клавіша: G",
		"wt_prev": "попередній трек$NГаряча клавіша: J",
		"wt_play": "відтворити / пауза$NГаряча клавіша: P",
		"wt_next": "наступний трек$NГаряча клавіша: L",

		"ul_par": "паралельні завантаження:",
		"ut_rand": "випадкові імена файлів",
		"ut_u2ts": "копіювати часову мітку останньої зміни$Nз вашої файлової системи на сервер\">📅",
		"ut_ow": "перезаписати існуючі файли на сервері?$N🛡️: ніколи (замість цього створить нове ім'я файлу)$N🕒: перезаписати, якщо файл на сервері старіший за ваш$N♻️: завжди перезаписувати, якщо файли відрізняються",
		"ut_mt": "продовжувати хешування інших файлів під час завантаження$N$Nможливо, вимкніть, якщо ваш CPU або HDD є вузьким місцем",
		"ut_ask": 'запитати підтвердження перед початком завантаження">💭',
		"ut_pot": "покращити швидкість завантаження на повільних пристроях$Nроблячи інтерфейс менш складним",
		"ut_srch": "не завантажувати, а перевірити, чи файли вже $N існують на сервері (сканує всі папки, які ви можете читати)",
		"ut_par": "призупинити завантаження, встановивши 0$N$Nзбільшіть, якщо ваше з'єднання повільне / висока затримка$N$Nзалишіть 1 в локальній мережі або якщо HDD сервера є вузьким місцем",
		"ul_btn": "перетягніть файли / папки<br> (або клацніть сюди)",
		"ul_btnu": "ЗАВАНТАЖИТИ",
		"ul_btns": "П О Ш У К",

		"ul_hash": "хеш",
		"ul_send": "надіслати",
		"ul_done": "готово",
		"ul_idle1": "завантаження ще не поставлені в чергу",
		"ut_etah": "середня швидкість &lt;em&gt;хешування&lt;/em&gt; і орієнтовний час до завершення",
		"ut_etau": "середня швидкість &lt;em&gt;завантаження&lt;/em&gt; і орієнтовний час до завершення",
		"ut_etat": "середня &lt;em&gt;загальна&lt;/em&gt; швидкість і орієнтовний час до завершення",

		"uct_ok": "успішно завершено",
		"uct_ng": "невдало: помилка / відхилено / не знайдено",
		"uct_done": "ok і ng разом",
		"uct_bz": "хешування або завантаження",
		"uct_q": "очікує, в черзі",

		"utl_name": "ім'я файлу",
		"utl_ulist": "список",
		"utl_ucopy": "копіювати",
		"utl_links": "посилання",
		"utl_stat": "статус",
		"utl_prog": "прогрес",

		// keep short:
		"utl_404": "404",
		"utl_err": "ПОМИЛКА",
		"utl_oserr": "помилка ОС",
		"utl_found": "знайдено",
		"utl_defer": "відкласти",
		"utl_yolo": "YOLO",
		"utl_done": "готово",

		"ul_flagblk": "файли були додані до черги</b><br>однак є зайнятий up2k в іншій вкладці браузера,<br>тому чекаємо, поки він завершиться спочатку",
		"ul_btnlk": "конфігурація сервера заблокувала цей перемикач у цьому стані",

		"udt_up": "Завантаження",
		"udt_srch": "Пошук",
		"udt_drop": "перетягніть сюди",

		"u_nav_m": '<h6>гаразд, що у вас є?</h6><code>Enter</code> = Файли (один або більше)\n<code>ESC</code> = Одна папка (включаючи підпапки)',
		"u_nav_b": '<a href="#" id="modal-ok">Файли</a><a href="#" id="modal-ng">Одна папка</a>',

		"cl_opts": "перемикачі",
		"cl_themes": "тема",
		"cl_langs": "мова",
		"cl_ziptype": "завантаження папки",
		"cl_uopts": "перемикачі up2k",
		"cl_favico": "favicon",
		"cl_bigdir": "великі папки",
		"cl_hsort": "#сортування",
		"cl_keytype": "позначення клавіш",
		"cl_hiddenc": "приховані стовпці",
		"cl_hidec": "приховати",
		"cl_reset": "скинути",
		"cl_hpick": "натисніть на заголовки стовпців, щоб приховати їх у таблиці нижче",
		"cl_hcancel": "приховання стовпців скасовано",

		"ct_grid": '田 сітка',
		"ct_ttips": '◔ ◡ ◔">ℹ️ підказки',
		"ct_thumb": 'у режимі сітки, перемкнути іконки або мініатюри$NГаряча клавіша: T">🖼️ мініатюри',
		"ct_csel": 'використовувати CTRL і SHIFT для вибору файлів у режимі сітки">вибір',
		"ct_ihop": 'коли переглядач зображень закрито, прокрутити вниз до останнього переглянутого файлу">g⮯',
		"ct_dots": 'показати приховані файли (якщо сервер дозволяє)">приховані файли',
		"ct_qdel": 'при видаленні файлів, запитати підтвердження лише один раз">швидке видалення',
		"ct_dir1st": 'сортувати папки перед файлами">спочатку 📁',
		"ct_nsort": 'природне сортування (для імен файлів з початковими цифрами)">природне сортування',
		"ct_utc": 'використовуйте UTC для всіх часових позначень">UTC', //m
		"ct_readme": 'показати README.md у списках папок">📜 readme',
		"ct_idxh": 'показати index.html замість списку папки">htm',
		"ct_sbars": 'показати смуги прокрутки">⟊',

		"cut_umod": "якщо файл вже існує на сервері, оновити часову мітку останньої зміни сервера відповідно до вашого локального файлу (потребує дозволів на запис+видалення)\">re📅",

		"cut_turbo": "кнопка yolo, ви, ймовірно, НЕ хочете її вмикати:$N$Nвикористовуйте це, якщо ви завантажували величезну кількість файлів і змушені були перезапустити з якоїсь причини, і хочете продовжити завантаження якнайшвидше$N$Nце замінює перевірку хешу простою <em>&quot;чи має цей файл той самий розмір на сервері?&quot;</em>, тому якщо вміст файлу відрізняється, він НЕ буде завантажений$N$Nви повинні вимкнути це, коли завантаження буде завершено, а потім &quot;завантажити&quot; ті самі файли знову, щоб дозволити клієнту перевірити їх\">turbo",

		"cut_datechk": "не має ефекту, якщо кнопка turbo не ввімкнена$N$Nзменшує yolo фактор на крихту; перевіряє, чи відповідають часові мітки файлів на сервері вашим$N$N<em>теоретично</em>, повинно зловити більшість незавершених / пошкоджених завантажень, але не є заміною виконання перевірки з вимкненим turbo потім\">date-chk",

		"cut_u2sz": "розмір (у MiB) кожного фрагмента завантаження; великі значення краще летять через атлантичний океан. Спробуйте низькі значення на дуже ненадійних з'єднаннях",

		"cut_flag": "переконатися, що лише одна вкладка завантажує одночасно $N -- інші вкладки також повинні мати це ввімкнене $N -- впливає лише на вкладки на тому самому домені",

		"cut_az": "завантажувати файли в алфавітному порядку, а не від найменшого файлу$N$Nалфавітний порядок може полегшити огляд, якщо щось пішло не так на сервері, але робить завантаження трохи повільнішим на fiber / LAN",

		"cut_nag": "сповіщення ОС після завершення завантаження$N(тільки якщо браузер або вкладка не активні)",
		"cut_sfx": "звуковий сигнал після завершення завантаження$N(тільки якщо браузер або вкладка не активні)",

		"cut_mt": "використовувати багатопотоковість для прискорення хешування файлів$N$Nце використовує веб-воркери і потребує$Nбільше пам'яті (до 512 MiB додатково)$N$Nробить https на 30% швидше, http у 4.5 рази швидше\">mt",

		"cut_wasm": "використовувати wasm замість вбудованого хешера браузера; покращує швидкість у браузерах на базі chrome, але збільшує навантаження CPU, плюс багато старих версій chrome мають баги, які змушують браузер споживати всю пам'ять і вилітати, якщо ця опція ввімкненаа\">wasm",

		"cft_text": "текст favicon (порожній і оновити для відключення)",
		"cft_fg": "колір переднього плану",
		"cft_bg": "колір фону",

		"cdt_lim": "максимальна кількість файлів для показу в папці",
		"cdt_ask": "при прокрутці до низу,$Nзамість завантаження більше файлів,$Nзапитати, що робити",
		"cdt_hsort": "скільки правил сортування (&lt;code&gt;,sorthref&lt;/code&gt;) включати в медіа-URL. Встановлення цього в 0 також буде ігнорувати правила сортування, включені в медіа посилання при їх натисканні",

		"tt_entree": "показати панель навігації (бічна панель дерева каталогів)$NГаряча клавіша: B",
		"tt_detree": "показати хлібні крихти$NГаряча клавіша: B",
		"tt_visdir": "прокрутити до вибраної папки",
		"tt_ftree": "перемкнути дерево папок / текстові файли$NГаряча клавіша: V",
		"tt_pdock": "показати батьківські папки в закріпленій панелі зверху",
		"tt_dynt": "автоматично збільшуватися при розширенні дерева",
		"tt_wrap": "перенесення слів",
		"tt_hover": "показувати переповнені рядки при наведенні$N( порушує прокрутку, якщо курсор $N&nbsp; миші не знаходиться в лівому відступі )",

		"ml_pmode": "в кінці папки...",
		"ml_btns": "команди",
		"ml_tcode": "транскодувати",
		"ml_tcode2": "транскодувати в",
		"ml_tint": "відтінок",
		"ml_eq": "аудіо еквалайзер",
		"ml_drc": "компресор динамічного діапазону",

		"mt_loop": "зациклити/повторити одну пісню\">🔁",
		"mt_one": "зупинити після однієї пісні\">1️⃣",
		"mt_shuf": "перемішати пісні в кожній папці\">🔀",
		"mt_aplay": "автовідтворення, якщо є ID пісні в посиланні, по якому ви клацнули для доступу до сервера$N$Nвідключення цього також зупинить оновлення URL сторінки з ID пісень під час відтворення музики, щоб запобігти автовідтворенню, якщо ці налаштування втрачені, але URL залишається\">a▶",
		"mt_preload": "почати завантаження наступної пісні ближче до кінця для безперервного відтворення\">preload",
		"mt_prescan": "перейти до наступної папки перед тим, як остання пісня$Nзакінчиться, підтримуючи веб-браузер у робочому стані$Nщоб він не зупинив відтворення\">nav",
		"mt_fullpre": "спробувати попередньо завантажити всю пісню;$N✅ увімкніть на <b>ненадійних</b> з'єднаннях,$N❌ <b>вимкніть</b> на повільних з'єднаннях, ймовірно\">full",
		"mt_fau": "на телефонах, запобігти зупинці музики, якщо наступна пісня не завантажується достатньо швидко (може зробити відображення тегів глючним)\">☕️",
		"mt_waves": "смуга хвильової форми:$Nпоказати амплітуду аудіо в повзунку\">~s",
		"mt_npclip": "показати кнопки для копіювання до буфера поточної пісні, що відтворюється\">/np",
		"mt_m3u_c": "показати кнопки для копіювання до буфера$Nвибраних пісень як записи плейлисту m3u8\">📻",
		"mt_octl": "інтеграція з ОС (медіа гарячі клавіші / osd)\">os-ctl",
		"mt_oseek": "дозволити перемотування через інтеграцію з ОС$N$Nзауваження: на деяких пристроях (iPhone),$Nце замінює кнопку наступної пісні\">seek",
		"mt_oscv": "показати обкладинку альбому в osd\">art",
		"mt_follow": "тримати трек, що відтворюється, у полі зору\">🎯",
		"mt_compact": "компактні елементи керування\">⟎",
		"mt_uncache": "очистити кеш &nbsp;(спробуйте це, якщо ваш браузер закешував$Nпошкоджену копію пісні, тому відмовляється її відтворювати)\">uncache",
		"mt_mloop": "зациклити відкриту папку\">🔁 loop",
		"mt_mnext": "завантажити наступну папку і продовжити\">📂 next",
		"mt_mstop": "зупинити відтворення\">⏸ stop",
		"mt_cflac": "конвертувати flac / wav в {0}\">flac",
		"mt_caac": "конвертувати aac / m4a в {0}\">aac",
		"mt_coth": "конвертувати всі інші (не mp3) в {0}\">oth",
		"mt_c2opus": "найкращий вибір для робочих столів, ноутбуків, android\">opus",
		"mt_c2owa": "opus-weba, для iOS 17.5 і новіших\">owa",
		"mt_c2caf": "opus-caf, для iOS 11 до 17\">caf",
		"mt_c2mp3": "використовуйте це на дуже старих пристроях\">mp3",
		"mt_c2flac": "найкраща якість звуку, але великі завантаження\">flac", //m
		"mt_c2wav": "відтворення без стиснення (ще більше)\">wav", //m
		"mt_c2ok": "гарно, хороший вибір",
		"mt_c2nd": "це не рекомендований вихідний формат для вашого пристрою, але це нормально",
		"mt_c2ng": "ваш пристрій, здається, не підтримує цей вихідний формат, але давайте все одно спробуємо",
		"mt_xowa": "є баги в iOS, які запобігають фоновому відтворенню з використанням цього формату; будь ласка, використовуйте caf або mp3 замість цього",
		"mt_tint": "рівень фону (0-100) на смузі перемотування$Nщоб зробити буферизацію менш відвертаючою",
		"mt_eq": "вмикає еквалайзер і контроль посилення;$N$Nпосилення &lt;code&gt;0&lt;/code&gt; = стандартна 100% гучність (немодифікована)$N$Nширина &lt;code&gt;1 &nbsp;&lt;/code&gt; = стандартне стерео (немодифіковане)$Nширина &lt;code&gt;0.5&lt;/code&gt; = 50% перехресне живлення ліво-право$Nширина &lt;code&gt;0 &nbsp;&lt;/code&gt; = моно$N$Nпосилення &lt;code&gt;-0.8&lt;/code&gt; &amp; ширина &lt;code&gt;10&lt;/code&gt; = видалення вокалу :^)$N$Nвключення еквалайзера робить безшовні альбоми повністю безшовними, тому залишайте його увімкненим з усіма значеннями в нулі (окрім ширини = 1), якщо вам це важливо",
		"mt_drc": "вмикає компресор динамічного діапазону (вирівнювач гучності / цегловий вал); також увімкне EQ для балансування спагеті, тому встановіть всі поля EQ окрім 'width' в 0, якщо ви цього не хочете$N$Nзнижує гучність аудіо вище THRESHOLD дБ; для кожного RATIO дБ понад THRESHOLD є 1 дБ виходу, тому стандартні значення tresh -24 і ratio 12 означають, що він ніколи не повинен стати гучнішим за -22 дБ і безпечно збільшити посилення еквалайзера до 0.8, або навіть 1.8 з ATK 0 і величезним RLS як 90 (працює тільки в firefox; RLS максимум 1 в інших браузерах)$N$N(дивіться вікіпедію, вони пояснюють це набагато краще)",

		"mb_play": "відтворити",
		"mm_hashplay": "відтворити цей аудіо файл?",
		"mm_m3u": "натисніть <code>Enter/Гаразд</code> для відтворення\nнатисніть <code>ESC/Скасувати</code> для редагування",
		"mp_breq": "потрібен firefox 82+ або chrome 73+ або iOS 15+",
		"mm_bload": "зараз завантажується...",
		"mm_bconv": "конвертується в {0}, будь ласка, зачекайте...",
		"mm_opusen": "ваш браузер не може відтворювати aac / m4a файли;\nтранскодування в opus тепер увімкнено",
		"mm_playerr": "відтворення невдале: ",
		"mm_eabrt": "Спроба відтворення була скасована",
		"mm_enet": "Ваше інтернет-з'єднання нестабільне",
		"mm_edec": "Цей файл нібито пошкоджений??",
		"mm_esupp": "Ваш браузер не розуміє цей аудіо формат",
		"mm_eunk": "Невідома помилка",
		"mm_e404": "Не вдалося відтворити аудіо; помилка 404: Файл не знайдено.",
		"mm_e403": "Не вдалося відтворити аудіо; помилка 403: Доступ заборонено.\n\nСпробуйте натиснути F5 для перезавантаження, можливо, ви вийшли з системи",
		"mm_e500": "Не вдалося відтворити аудіо; помилка 500: Перевірте логи сервера.",
		"mm_e5xx": "Не вдалося відтворити аудіо; помилка сервера ",
		"mm_nof": "не знаходжу більше аудіо файлів поблизу",
		"mm_prescan": "Шукаю музику для наступного відтворення...",
		"mm_scank": "Знайшов наступну пісню:",
		"mm_uncache": "кеш очищено; всі пісні будуть перезавантажені при наступному відтворенні",
		"mm_hnf": "ця пісня більше не існує",

		"im_hnf": "це зображення більше не існує",

		"f_empty": 'ця папка порожня',
		"f_chide": 'це приховає стовпець «{0}»\n\nви можете показати стовпці в вкладці налаштувань',
		"f_bigtxt": "цей файл розміром {0} MiB -- дійсно переглядати як текст?",
		"f_bigtxt2": "переглянути лише кінець файлу замість цього? це також увімкне відслідковування/tailing, показуючи новододані рядки тексту в реальному часі",
		"fbd_more": '<div id="blazy">показано <code>{0}</code> з <code>{1}</code> файлів; <a href="#" id="bd_more">показати {2}</a> або <a href="#" id="bd_all">показати всі</a></div>',
		"fbd_all": '<div id="blazy">показано <code>{0}</code> з <code>{1}</code> файлів; <a href="#" id="bd_all">показати всі</a></div>',
		"f_anota": "лише {0} з {1} елементів було вибрано;\nщоб вибрати всю папку, спочатку прокрутіть до низу",

		"f_dls": 'посилання на файли в поточній папці були\nзмінені на посилання для завантаження',

		"f_partial": "Щоб безпечно завантажити файл, який зараз завантажується, будь ласка, клацніть на файл, який має таке саме ім'я, але без розширення <code>.PARTIAL</code>. Будь ласка, натисніть Скасувати або Escape, щоб зробити це.\n\nНатиснення Гаразд / Enter проігнорує це попередження і продовжить завантаження <code>.PARTIAL</code> робочого файлу замість цього, що майже напевно дасть вам пошкоджені дані.",

		"ft_paste": "вставити {0} елементів$NГаряча клавіша: ctrl-V",
		"fr_eperm": 'не можу перейменувати:\nу вас немає дозволу “переміщення“ в цій папці',
		"fd_eperm": 'не можу видалити:\nу вас немає дозволу “видалення“ в цій папці',
		"fc_eperm": 'не можу вирізати:\nу вас немає дозволу “переміщення“ в цій папці',
		"fp_eperm": 'не можу вставити:\nу вас немає дозволу “запису“ в цій папці',
		"fr_emore": "виберіть принаймні один елемент для перейменування",
		"fd_emore": "виберіть принаймні один елемент для видалення",
		"fc_emore": "виберіть принаймні один елемент для вирізання",
		"fcp_emore": "виберіть принаймні один елемент для копіювання до буфера",

		"fs_sc": "поділитися папкою, в якій ви знаходитесь",
		"fs_ss": "поділитися вибраними файлами",
		"fs_just1d": "ви не можете вибрати більше однієї папки,\nабо змішувати файли і папки в одному виборі",
		"fs_abrt": "❌ скасувати",
		"fs_rand": "🎲 випадк.ім'я",
		"fs_go": "✅ створити спільний доступ",
		"fs_name": "ім'я",
		"fs_src": "джерело",
		"fs_pwd": "пароль",
		"fs_exp": "термін дії",
		"fs_tmin": "хв",
		"fs_thrs": "годин",
		"fs_tdays": "днів",
		"fs_never": "вічний",
		"fs_pname": "необов'язкове ім'я посилання; буде випадковим, якщо порожнє",
		"fs_tsrc": "файл або папка для спільного доступу",
		"fs_ppwd": "необов'язковий пароль",
		"fs_w8": "створення спільного доступу...",
		"fs_ok": "натисніть <code>Enter/Гаразд</code> для копіювання до буфера\nнатисніть <code>ESC/Скасувати</code> для закриття",

		"frt_dec": "може виправити деякі випадки пошкоджених імен файлів\">url-decode",
		"frt_rst": "скинути змінені імена файлів назад до оригінальних\">↺ reset",
		"frt_abrt": "перервати і закрити це вікно\">❌ cancel",
		"frb_apply": "ЗАСТОСУВАТИ ПЕРЕЙМЕНУВАННЯ",
		"fr_adv": "пакетне / метадані / шаблонне перейменування\">розширене",
		"fr_case": "регулярний вираз з урахуванням регістру\">регістр",
		"fr_win": "безпечні для windows імена; замінити <code>&lt;&gt;:&quot;\\|?*</code> на японські повноширинні символи\">win",
		"fr_slash": "замінити <code>/</code> на символ, який не призводить до створення нових папок\">без /",
		"fr_re": "шаблон пошуку регулярного виразу для застосування до оригінальних імен файлів; групи захоплення можна посилатися в полі формату нижче як &lt;code&gt;(1)&lt;/code&gt; і &lt;code&gt;(2)&lt;/code&gt; і так далі",
		"fr_fmt": "натхненний foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; замінюється назвою пісні,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; пропускає [цю] частину, якщо виконавець порожній$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; доповнює номер треку до 2 цифр",
		"fr_pdel": "видалити",
		"fr_pnew": "зберегти як",
		"fr_pname": "надайте ім'я для вашого нового пресету",
		"fr_aborted": "перервано",
		"fr_lold": "старе ім'я",
		"fr_lnew": "нове ім'я",
		"fr_tags": "теги для вибраних файлів (тільки для читання, лише для довідки):",
		"fr_busy": "перейменування {0} елементів...\n\n{1}",
		"fr_efail": "перейменування невдале:\n",
		"fr_nchg": "{0} з нових імен були змінені через <code>win</code> та/або <code>no /</code>\n\nOK продовжити з цими зміненими новими іменами?",

		"fd_ok": "видалення OK",
		"fd_err": "видалення невдале:\n",
		"fd_none": "нічого не було видалено; можливо, заблоковано конфігурацією сервера (xbd)?",
		"fd_busy": "видалення {0} елементів...\n\n{1}",
		"fd_warn1": "ВИДАЛИТИ ці {0} елементи?",
		"fd_warn2": "<b>Останній шанс!</b> Неможливо скасувати. Видалити?",

		"fc_ok": "вирізано {0} елементів",
		"fc_warn": 'вирізано {0} елементів\n\nале: тільки <b>ця</b> вкладка браузера може їх вставити\n(оскільки вибір настільки величезний)',

		"fcc_ok": "скопійовано {0} елементів до буфера",
		"fcc_warn": 'скопійовано {0} елементів до буфера\n\nале: тільки <b>ця</b> вкладка браузера може їх вставити\n(оскільки вибір настільки величезний)',

		"fp_apply": "використовувати ці імена",
		"fp_ecut": "спочатку вирізати або скопіювати деякі файли / папки для вставки / переміщення\n\nзауваження: ви можете вирізати / вставляти через різні вкладки браузера",
		"fp_ename": "{0} елементів не можуть бути переміщені сюди, тому що імена вже зайняті. Дайте їм нові імена нижче для продовження, або залиште ім'я порожнім, щоб пропустити їх:",
		"fcp_ename": "{0} елементів не можуть бути скопійовані сюди, тому що імена вже зайняті. Дайте їм нові імена нижче для продовження, або залиште ім'я порожнім, щоб пропустити їх:",
		"fp_emore": "є ще деякі конфлікти імен файлів, які потрібно виправити",
		"fp_ok": "переміщення OK",
		"fcp_ok": "копіювання OK",
		"fp_busy": "переміщення {0} елементів...\n\n{1}",
		"fcp_busy": "копіювання {0} елементів...\n\n{1}",
		"fp_abrt": "переривання...", //m
		"fp_err": "переміщення невдале:\n",
		"fcp_err": "копіювання невдале:\n",
		"fp_confirm": "перемістити ці {0} елементи сюди?",
		"fcp_confirm": "скопіювати ці {0} елементи сюди?",
		"fp_etab": 'не вдалося прочитати буфер з іншої вкладки браузера',
		"fp_name": "завантаження файлу з вашого пристрою. Дайте йому ім'я:",
		"fp_both_m": '<h6>виберіть, що вставити</h6><code>Enter</code> = Перемістити {0} файлів з «{1}»\n<code>ESC</code> = Завантажити {2} файлів з вашого пристрою',
		"fcp_both_m": '<h6>виберіть, що вставити</h6><code>Enter</code> = Скопіювати {0} файлів з «{1}»\n<code>ESC</code> = Завантажити {2} файлів з вашого пристрою',
		"fp_both_b": '<a href="#" id="modal-ok">Перемістити</a><a href="#" id="modal-ng">Завантажити</a>',
		"fcp_both_b": '<a href="#" id="modal-ok">Скопіювати</a><a href="#" id="modal-ng">Завантажити</a>',

		"mk_noname": "введіть ім'я в текстове поле зліва перед тим, як робити це :p",

		"tv_load": "Завантаження текстового документа:\n\n{0}\n\n{1}% ({2} з {3} MiB завантажено)",
		"tv_xe1": "не вдалося завантажити текстовий файл:\n\nпомилка ",
		"tv_xe2": "404, файл не знайдено",
		"tv_lst": "список текстових файлів в",
		"tvt_close": "повернутися до перегляду папки$NГаряча клавіша: M (або Esc)\">❌ закрити",
		"tvt_dl": "завантажити цей файл$NГаряча клавіша: Y\">💾 завантажити",
		"tvt_prev": "показати попередній документ$NГаряча клавіша: i\">⬆ попер",
		"tvt_next": "показати наступний документ$NГаряча клавіша: K\">⬇ наст",
		"tvt_sel": "вибрати файл &nbsp; ( для вирізання / копіювання / видалення / ... )$NГаряча клавіша: S\">вибр",
		"tvt_edit": "відкрити файл в текстовому редакторі$NГаряча клавіша: E\">✏️ редагувати",
		"tvt_tail": "моніторити файл на зміни; показувати нові рядки в реальному часі\">📡 слідкувати",
		"tvt_wrap": "перенесення слів\">↵",
		"tvt_atail": "заблокувати прокрутку до низу сторінки\">⚓",
		"tvt_ctail": "декодувати кольори терміналу (ansi escape коди)\">🌈",
		"tvt_ntail": "ліміт історії прокрутки (скільки байтів тексту тримати завантаженими)",

		"m3u_add1": "пісня додана до m3u плейлисту",
		"m3u_addn": "{0} пісень додано до m3u плейлисту",
		"m3u_clip": "m3u плейлист тепер скопійований до буфера\n\nви повинні створити новий текстовий файл з назвою щось.m3u і вставити плейлист в цей документ; це зробить його відтворюваним",

		"gt_vau": "не показувати відео, лише відтворювати аудіо\">🎧",
		"gt_msel": "увімкнути вибір файлів; ctrl-клік по файлу для перевизначення$N$N&lt;em&gt;коли активний: подвійний клік по файлу / папці щоб відкрити&lt;/em&gt;$N$NГаряча клавіша: S\">мультивибір",
		"gt_crop": "обрізати мініатюри по центру\">обрізка",
		"gt_3x": "мініатюри високої роздільності\">3x",
		"gt_zoom": "масштаб",
		"gt_chop": "обрізати",
		"gt_sort": "сортувати за",
		"gt_name": "ім'ям",
		"gt_sz": "розміром",
		"gt_ts": "датою",
		"gt_ext": "типом",
		"gt_c1": "обрізати імена файлів більше (показувати менше)",
		"gt_c2": "обрізати імена файлів менше (показувати більше)",

		"sm_w8": "пошук...",
		"sm_prev": "результати пошуку нижче з попереднього запиту:\n  ",
		"sl_close": "закрити результати пошуку",
		"sl_hits": "показано {0} результатів",
		"sl_moar": "завантажити більше",

		"s_sz": "розмір",
		"s_dt": "дата",
		"s_rd": "шлях",
		"s_fn": "ім'я",
		"s_ta": "теги",
		"s_ua": "up@",
		"s_ad": "розш.",
		"s_s1": "мінімум MiB",
		"s_s2": "максимум MiB",
		"s_d1": "мін. iso8601",
		"s_d2": "макс. iso8601",
		"s_u1": "завантажено після",
		"s_u2": "та/або до",
		"s_r1": "шлях містить &nbsp; (розділені пробілами)",
		"s_f1": "ім'я містить &nbsp; (заперечення з -ні)",
		"s_t1": "теги містять &nbsp; (^=початок, кінець=$)",
		"s_a1": "специфічні властивості метаданих",

		"md_eshow": "не можу відобразити ",
		"md_off": "[📜<em>readme</em>] відключено в [⚙️] -- документ прихований",

		"badreply": "Не вдалося обробити відповідь сервера",

		"xhr403": "403: Доступ заборонено\n\nспробуйте натиснути F5, можливо ви вийшли з системи",
		"xhr0": "невідома (ймовірно втрачено з'єднання з сервером, або сервер офлайн)",
		"cf_ok": "вибачте за це -- захист від DD" + wah + "oS спрацював\n\nречі повинні відновитися приблизно через 30 сек\n\nякщо нічого не відбувається, натисніть F5 для перезавантаження сторінки",
		"tl_xe1": "не вдалося перелічити підпапки:\n\nпомилка ",
		"tl_xe2": "404: Папка не знайдена",
		"fl_xe1": "не вдалося перелічити файли в папці:\n\nпомилка ",
		"fl_xe2": "404: Папка не знайдена",
		"fd_xe1": "не вдалося створити підпапку:\n\nпомилка ",
		"fd_xe2": "404: Батьківська папка не знайдена",
		"fsm_xe1": "не вдалося надіслати повідомлення:\n\nпомилка ",
		"fsm_xe2": "404: Батьківська папка не знайдена",
		"fu_xe1": "не вдалося завантажити список unpost з сервера:\n\nпомилка ",
		"fu_xe2": "404: Файл не знайдено??",

		"fz_tar": "нестиснутий gnu-tar файл (linux / mac)",
		"fz_pax": "нестиснутий tar в pax-форматі (повільніше)",
		"fz_targz": "gnu-tar зі стисненням gzip рівня 3$N$Nце зазвичай дуже повільно, тому$Nвикористовуйте нестиснутий tar замість цього",
		"fz_tarxz": "gnu-tar зі стисненням xz рівня 1$N$Nце зазвичай дуже повільно, тому$Nвикористовуйте нестиснутий tar замість цього",
		"fz_zip8": "zip з utf8 іменами файлів (можливо нестабільний на windows 7 і старіших)",
		"fz_zipd": "zip з традиційними cp437 іменами файлів, для дуже старого ПЗ",
		"fz_zipc": "cp437 з crc32, обчисленим заздалегідь,$Nдля MS-DOS PKZIP v2.04g (жовтень 1993)$N(потребує більше часу для обробки перед початком завантаження)",

		"un_m1": "ви можете видалити ваші недавні завантаження (або перервати незавершені) нижче",
		"un_upd": "оновити",
		"un_m4": "або поділитися файлами, видимими нижче:",
		"un_ulist": "показати",
		"un_ucopy": "копіювати",
		"un_flt": "необов'язковий фільтр:&nbsp; URL повинен містити",
		"un_fclr": "очистити фільтр",
		"un_derr": 'unpost-видалення невдале:\n',
		"un_f5": 'щось зламалося, будь ласка, спробуйте оновити або натисніть F5',
		"un_uf5": "вибачте, але ви повинні оновити сторінку (наприклад, натиснувши F5 або CTRL-R) перед тим, як це завантаження можна буде перервати",
		"un_nou": '<b>попередження:</b> сервер занадто зайнятий, щоб показати незавершені завантаження; клацніть посилання "оновити" трохи пізніше',
		"un_noc": '<b>попередження:</b> unpost повністю завантажених файлів не увімкнено/дозволено в конфігурації сервера',
		"un_max": "показано перші 2000 файлів (використовуйте фільтр)",
		"un_avail": "{0} недавніх завантажень можуть бути видалені<br />{1} незавершених можуть бути перервані",
		"un_m2": "відсортовано за часом завантаження; найновіші спочатку:",
		"un_no1": "ха! немає завантажень, достатньо недавніх",
		"un_no2": "ха! немає завантажень, що відповідають цьому фільтру, достатньо недавніх",
		"un_next": "видалити наступні {0} файлів нижче",
		"un_abrt": "перервати",
		"un_del": "видалити",
		"un_m3": "завантаження ваших недавніх завантажень...",
		"un_busy": "видалення {0} файлів...",
		"un_clip": "{0} посилань скопійовано до буфера",

		"u_https1": "вам слід",
		"u_https2": "переключитися на https",
		"u_https3": "для кращої продуктивності",
		"u_ancient": 'ваш браузер вражаюче старий -- можливо, вам слід <a href="#" onclick="goto(\'bup\')">використовувати bup замість цього</a>',
		"u_nowork": "потрібен firefox 53+ або chrome 57+ або iOS 11+",
		"tail_2old": "потрібен firefox 105+ або chrome 71+ або iOS 14.5+",
		"u_nodrop": 'ваш браузер занадто старий для перетягування завантажень',
		"u_notdir": "це не папка!\n\nваш браузер занадто старий,\nбудь ласка, спробуйте перетягування замість цього",
		"u_uri": "щоб перетягнути зображення з інших вікон браузера,\nбудь ласка, перетягніть його на велику кнопку завантаження",
		"u_enpot": 'переключитися на <a href="#">картоплинний UI</a> (може покращити швидкість завантаження)',
		"u_depot": 'переключитися на <a href="#">вишуканий UI</a> (може зменшити швидкість завантаження)',
		"u_gotpot": 'переключення на картоплинний UI для покращення швидкості завантаження,\n\nне соромтеся не погодитися і переключитися назад!',
		"u_pott": "<p>файли: &nbsp; <b>{0}</b> завершено, &nbsp; <b>{1}</b> невдало, &nbsp; <b>{2}</b> зайнято, &nbsp; <b>{3}</b> в черзі</p>",
		"u_ever": "це базовий завантажувач; up2k потребує принаймні<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'це базовий завантажувач; <a href="#" id="u2yea">up2k</a> кращий',
		"u_uput": 'оптимізувати для швидкості (пропустити контрольну суму)',
		"u_ewrite": 'у вас немає доступу для запису в цю папку',
		"u_eread": 'у вас немає доступу для читання цієї папки',
		"u_enoi": 'пошук файлів не увімкнено в конфігурації сервера',
		"u_enoow": "перезапис не працюватиме тут; потрібен дозвіл на видалення",
		"u_badf": 'Ці {0} файли (з {1} загальних) були пропущені, можливо, через дозволи файлової системи:\n\n',
		"u_blankf": 'Ці {0} файли (з {1} загальних) порожні; все одно завантажити їх?\n\n',
		"u_applef": 'Ці {0} файли (з {1} загальних), ймовірно, небажані;\nНатисніть <code>Гаразд/Enter</code> щоб ПРОПУСТИТИ наступні файли,\nНатисніть <code>Скасувати/ESC</code> щоб НЕ виключати, і ЗАВАНТАЖИТИ їх також:\n\n',
		"u_just1": '\nМожливо, це спрацює краще, якщо ви виберете лише один файл',
		"u_ff_many": "якщо ви використовуєте <b>Linux / MacOS / Android,</b> то така кількість файлів <a href=\"https://bugzilla.mozilla.org/show_bug.cgi?id=1790500\" target=\"_blank\"><em>може</em> завісити Firefox!</a>\nякщо це станеться, будь ласка, спробуйте знову (або використовуйте Chrome).",
		"u_up_life": "Це завантаження буде видалено з сервера\n{0} після його завершення",
		"u_asku": 'завантажити ці {0} файлів до <code>{1}</code>',
		"u_unpt": "ви можете скасувати / видалити це завантаження, використовуючи 🧯 зверху зліва",
		"u_bigtab": 'збираюся показати {0} файлів\n\nце може завісити ваш браузер, ви впевнені?',
		"u_scan": 'Сканування файлів...',
		"u_dirstuck": 'ітератор каталогу застряг, намагаючись отримати доступ до наступних {0} елементів; пропущу:',
		"u_etadone": 'Готово ({0}, {1} файлів)',
		"u_etaprep": '(підготовка до завантаження)',
		"u_hashdone": 'хешування завершено',
		"u_hashing": 'хешування',
		"u_hs": 'рукостискання...',
		"u_started": "файли тепер завантажуються; дивіться [🚀]",
		"u_dupdefer": "дублікат; буде оброблено після всіх інших файлів",
		"u_actx": "клацніть цей текст, щоб запобігти втраті<br />продуктивності при переключенні на інші вікна/вкладки",
		"u_fixed": "OK!&nbsp; Виправлено 👍",
		"u_cuerr": "не вдалося завантажити фрагмент {0} з {1};\nймовірно, нешкідливо, продовжую\n\nфайл: {2}",
		"u_cuerr2": "сервер відхилив завантаження (фрагмент {0} з {1});\nспробую пізніше\n\nфайл: {2}\n\nпомилка ",
		"u_ehstmp": "спробую знову; дивіться внизу справа",
		"u_ehsfin": "сервер відхилив запит на завершення завантаження; повторюю...",
		"u_ehssrch": "сервер відхилив запит на виконання пошуку; повторюю...",
		"u_ehsinit": "сервер відхилив запит на ініціацію завантаження; повторюю...",
		"u_eneths": "мережева помилка під час виконання рукостискання завантаження; повторюю...",
		"u_enethd": "мережева помилка під час тестування існування цілі; повторюю...",
		"u_cbusy": "чекаємо, поки сервер знову нам довірятиме після мережевого збою...",
		"u_ehsdf": "на сервері закінчилося місце на диску!\n\nбуду продовжувати спроби, на випадок, якщо хтось\nзвільнить достатньо місця для продовження",
		"u_emtleak1": "схоже, ваш веб-браузер може мати витік пам'яті;\nбудь ласка,",
		"u_emtleak2": ' <a href="{0}">переключіться на https (рекомендується)</a> або ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'спробуйте наступне:\n<ul><li>натисніть <code>F5</code> для оновлення сторінки</li><li>потім відключіть кнопку &nbsp;<code>mt</code>&nbsp; в &nbsp;<code>⚙️ налаштуваннях</code></li><li>і спробуйте це завантаження знову</li></ul>Завантаження будуть трохи повільнішими, але що поробиш.\nВибачте за незручності !\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816" target="_blank">має виправлення</a> для цього',
		"u_emtleakf": 'спробуйте наступне:\n<ul><li>натисніть <code>F5</code> для оновлення сторінки</li><li>потім увімкніть <code>🥔</code> (картопля) в UI завантаження<li>і спробуйте це завантаження знову</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500" target="_blank">сподіваємося, матиме виправлення</a> в якийсь момент',
		"u_s404": "не знайдено на сервері",
		"u_expl": "пояснити",
		"u_maxconn": "більшість браузерів обмежують це до 6, але firefox дозволяє підвищити це з <code>connections-per-server</code> в <code>about:config</code>",
		"u_tu": '<p class="warn">ПОПЕРЕДЖЕННЯ: turbo увімкнено, <span>&nbsp;клієнт може не виявити і поновити неповні завантаження; дивіться підказку turbo-кнопки</span></p>',
		"u_ts": '<p class="warn">ПОПЕРЕДЖЕННЯ: turbo увімкнено, <span>&nbsp;результати пошуку можуть бути неправильними; дивіться підказку turbo-кнопки</span></p>',
		"u_turbo_c": "turbo відключено в конфігурації сервера",
		"u_turbo_g": "відключаю turbo, тому що у вас немає\nпривілеїв перегляду каталогів в цьому томі",
		"u_life_cfg": 'автовидалення через <input id="lifem" p="60" /> хв (або <input id="lifeh" p="3600" /> годин)',
		"u_life_est": 'завантаження буде видалено <span id="lifew" tt="місцевий час">---</span>',
		"u_life_max": 'ця папка забезпечує\nмакс. термін життя {0}',
		"u_unp_ok": 'unpost дозволено для {0}',
		"u_unp_ng": 'unpost НЕ буде дозволено',
		"ue_ro": 'ваш доступ до цієї папки тільки для читання\n\n',
		"ue_nl": 'ви зараз не увійшли в систему',
		"ue_la": 'ви зараз увійшли як "{0}"',
		"ue_sr": 'ви зараз в режимі пошуку файлів\n\nпереключіться на режим завантаження, клацнувши лупу 🔎 (поруч з великою кнопкою ПОШУК), і спробуйте завантажити знову\n\nвибачте',
		"ue_ta": 'спробуйте завантажити знову, це повинно спрацювати зараз',
		"ue_ab": "цей файл вже завантажується в іншу папку, і це завантаження повинно бути завершено перед тим, як файл можна буде завантажити в інше місце.\n\nВи можете перервати і забути початкове завантаження, використовуючи 🧯 зверху зліва",
		"ur_1uo": "OK: Файл успішно завантажено",
		"ur_auo": "OK: Всі {0} файлів успішно завантажено",
		"ur_1so": "OK: Файл знайдено на сервері",
		"ur_aso": "OK: Всі {0} файлів знайдено на сервері",
		"ur_1un": "Завантаження невдале, вибачте",
		"ur_aun": "Всі {0} завантажень невдалі, вибачте",
		"ur_1sn": "Файл НЕ знайдено на сервері",
		"ur_asn": "{0} файлів НЕ знайдено на сервері",
		"ur_um": "Завершено;\n{0} завантажень OK,\n{1} завантажень невдалих, вибачте",
		"ur_sm": "Завершено;\n{0} файлів знайдено на сервері,\n{1} файлів НЕ знайдено на сервері",

		"lang_set": "оновити сторінку, щоб зміни набули чинності?",
	},
};

var LANGS = ["eng", "nor", "chi", "cze", "deu", "epo", "fin", "fra", "grc", "ita", "kor", "nld", "nno", "pol", "por", "rus", "spa", "swe", "tur", "ukr"];

if (window.langmod)
	langmod();

for (var a = LANGS.length; a > 0;)
	if (!Ls[LANGS[--a]])
		LANGS.splice(a, 1);

var L = Ls[sread("cpp_lang", LANGS) || lang] ||
			Ls.eng || Ls.nor || Ls.chi;

for (var a = 0; a < LANGS.length; a++) {
	for (var b = a + 1; b < LANGS.length; b++) {
		var i1 = Object.keys(Ls[LANGS[a]]).length > Object.keys(Ls[LANGS[b]]).length ? a : b,
			i2 = i1 == a ? b : a,
			t1 = Ls[LANGS[i1]],
			t2 = Ls[LANGS[i2]];

		for (var k in t1)
			if (!t2[k] && !/^ht_.5$/.test(k)) {
				console.log("E missing TL", LANGS[i2], k);
				t2[k] = t1[k];
			}
	}
}

if (!has(LANGS, lang))
	alert('unsupported --lang "' + lang + '" specified in server args;\nplease use one of these: ' + LANGS);

modal.load();


// toolbar
ebi('ops').innerHTML = (
	'<a href="#" id="opa_x" data-dest="" tt="' + L.ot_close + '">--</a>' +
	'<a href="#" id="opa_srch" data-perm="read" data-dep="idx" data-dest="search" tt="' + L.ot_search + '">🔎</a>' +
	(have_del ? '<a href="#" id="opa_del" data-perm="write" data-dest="unpost" tt="' + L.ot_unpost + '">🧯</a>' : '') +
	'<a href="#" id="opa_up" data-dest="up2k">🚀</a>' +
	'<a href="#" id="opa_bup" data-perm="write" data-dest="bup" tt="' + L.ot_bup + '">🎈</a>' +
	'<a href="#" id="opa_mkd" data-perm="write" data-dest="mkdir" tt="' + L.ot_mkdir + '">📂</a>' +
	'<a href="#" id="opa_md" data-perm="read write" data-dest="new_md" tt="' + L.ot_md + '">📝</a>' +
	'<a href="#" id="opa_msg" data-dest="msg" tt="' + L.ot_msg + '">📟</a>' +
	'<a href="#" id="opa_auc" data-dest="player" tt="' + L.ot_mp + '">🎺</a>' +
	'<a href="#" id="opa_cfg" data-dest="cfg" tt="' + L.ot_cfg + '">⚙️</a>' +
	(IE ? '<span id="noie">' + L.ot_noie + '</span>' : '') +
	'<div id="opdesc"></div>'
);


// media player
ebi('widget').innerHTML = (
	'<div id="wtoggle">' +
	'<span id="wfs"></span>' +
	'<span id="wfm"><a' +
	' href="#" id="fshr" tt="' + L.wt_shr + '">📨<span>share</span></a><a' +
	' href="#" id="fren" tt="' + L.wt_ren + '">✎<span>name</span></a><a' +
	' href="#" id="fdel" tt="' + L.wt_del + '">⌫<span>del.</span></a><a' +
	' href="#" id="fcut" tt="' + L.wt_cut + '">✂<span>cut</span></a><a' +
	' href="#" id="fcpy" tt="' + L.wt_cpy + '">⧉<span>copy</span></a><a' +
	' href="#" id="fpst" tt="' + L.wt_pst + '">📋<span>paste</span></a>' +
	'</span><span id="wzip1"><a' +
	' href="#" id="zip1" tt="' + L.wt_zip1 + '">📦<span>zip</span></a>' +
	'</span><span id="wzip"><a' +
	' href="#" id="selall" tt="' + L.wt_selall + '">sel.<br />all</a><a' +
	' href="#" id="selinv" tt="' + L.wt_selinv + '">sel.<br />inv.</a><a' +
	' href="#" id="selzip" class="l1" tt="' + L.wt_selzip + '">zip</a><a' +
	' href="#" id="seldl" class="l1" tt="' + L.wt_seldl + '">dl</a>' +
	'</span><span id="wnp"><a' +
	' href="#" id="npirc" tt="' + L.wt_npirc + '">📋<span>irc</span></a><a' +
	' href="#" id="nptxt" tt="' + L.wt_nptxt + '">📋<span>txt</span></a>' +
	'</span><span id="wm3u"><a' +
	' href="#" id="m3ua" tt="' + L.wt_m3ua + '">📻<span>add</span></a><a' +
	' href="#" id="m3uc" tt="' + L.wt_m3uc + '">📻<span>copy</span></a>' +
	'</span><a' +
	'	href="#" id="wtgrid" tt="' + L.wt_grid + '">田</a><a' +
	'	href="#" id="wtico">♫</a>' +
	'</div>' +
	'<div id="widgeti">' +
	'	<div id="pctl"><a href="#" id="bprev" tt="' + L.wt_prev + '">⏮</a><a href="#" id="bplay" tt="' + L.wt_play + '">▶</a><a href="#" id="bnext" tt="' + L.wt_next + '">⏭</a></div>' +
	'	<canvas id="pvol" width="288" height="38"></canvas>' +
	'	<canvas id="barpos"></canvas>' +
	'	<canvas id="barbuf"></canvas>' +
	'</div>' +
	'<div id="np_inf">' +
	'	<img id="np_img" />' +
	'	<span id="np_url"></span>' +
	'	<span id="np_circle"></span>' +
	'	<span id="np_album"></span>' +
	'	<span id="np_tn"></span>' +
	'	<span id="np_artist"></span>' +
	'	<span id="np_title"></span>' +
	'	<span id="np_pos"></span>' +
	'	<span id="np_dur"></span>' +
	'</div>'
);


// up2k ui
ebi('op_up2k').innerHTML = (
	'<form id="u2form" method="post" enctype="multipart/form-data" onsubmit="return false;"></form>\n' +

	'<table id="u2conf">\n' +
	'	<tr>\n' +
	'		<td class="c" data-perm="read"><br />' + L.ul_par + '</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="multitask" />\n' +
	'			<label for="multitask" tt="' + L.ut_mt + '">🏃</label>\n' +
	'		</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="potato" />\n' +
	'			<label for="potato" tt="' + L.ut_pot + '">🥔</label>\n' +
	'		</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="u2rand" />\n' +
	'			<label for="u2rand" tt="' + L.ut_rand + '">🎲</label>\n' +
	'		</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="u2ow" />\n' +
	'			<label for="u2ow" tt="' + L.ut_ow + '">?</a>\n' +
	'		</td>\n' +
	'		<td class="c" data-perm="read" data-dep="idx" rowspan="2">\n' +
	'			<input type="checkbox" id="fsearch" />\n' +
	'			<label for="fsearch" tt="' + L.ut_srch + '">🔎</label>\n' +
	'		</td>\n' +
	'		<td data-perm="read" rowspan="2" id="u2btn_cw"></td>\n' +
	'		<td data-perm="read" rowspan="2" id="u2c3w"></td>\n' +
	'	</tr>\n' +
	'	<tr>\n' +
	'		<td class="c" data-perm="read">\n' +
	'			<a href="#" class="b" id="nthread_sub">&ndash;</a><input\n' +
	'				class="txtbox" id="nthread" value="" tt="' + L.ut_par + '"/><a\n' +
	'				href="#" class="b" id="nthread_add">+</a><br />&nbsp;\n' +
	'		</td>\n' +
	'	</tr>\n' +
	'</table>\n' +

	'<div id="u2notbtn"></div>\n' +

	'<div id="u2btn_ct">\n' +
	'	<div id="u2btn" tabindex="0">\n' +
	'		<span id="u2bm"></span>\n' + L.ul_btn +
	'	</div>\n' +
	'</div>\n' +

	'<div id="u2c3t">\n' +

	'<div id="u2etaw"><div id="u2etas"><div class="o">\n' +
	L.ul_hash + ': <span id="u2etah" tt="' + L.ut_etah + '">(' + L.ul_idle1 + ')</span><br />\n' +
	L.ul_send + ': <span id="u2etau" tt="' + L.ut_etau + '">(' + L.ul_idle1 + ')</span><br />\n' +
	'	</div><span class="o">' +
	L.ul_done + ': </span><span id="u2etat" tt="' + L.ut_etat + '">(' + L.ul_idle1 + ')</span>\n' +
	'</div></div>\n' +

	'<div id="u2cards">\n' +
	'	<a href="#" act="ok" tt="' + L.uct_ok + '">ok <span>0</span></a><a\n' +
	'	href="#" act="ng" tt="' + L.uct_ng + '">ng <span>0</span></a><a\n' +
	'	href="#" act="done" tt="' + L.uct_done + '">done <span>0</span></a><a\n' +
	'	href="#" act="bz" tt="' + L.uct_bz + '" class="act">busy <span>0</span></a><a\n' +
	'	href="#" act="q" tt="' + L.uct_q + '">que <span>0</span></a>\n' +
	'</div>\n' +

	'</div>\n' +

	'<div id="u2tabw" class="na"><table id="u2tab">\n' +
	'	<thead>\n' +
	'		<tr>\n' +
	'			<td>' + L.utl_name + ' &nbsp;(<a href="#" id="luplinks">' + L.utl_ulist + '</a>/<a href="#" id="cuplinks">' + L.utl_ucopy + '</a>' + L.utl_links + ')</td>\n' +
	'			<td>' + L.utl_stat + '</td>\n' +
	'			<td>' + L.utl_prog + '</td>\n' +
	'		</tr>\n' +
	'	</thead>\n' +
	'	<tbody></tbody>\n' +
	'</table><div id="u2mu"></div></div>\n' +

	'<p id="u2flagblock"><b>' + L.ul_flagblk + '</p>\n' +
	'<div id="u2life"></div>' +
	'<div id="u2foot"></div>'
);


ebi('wrap').insertBefore(mknod('div', 'lazy'), ebi('epi'));

var x = ebi('bbsw');
x.parentNode.insertBefore(mknod('div', null,
	'<input type="checkbox" id="uput" name="uput"><label for="uput">' + L.u_uput + '</label>'), x);


(function () {
	var o = mknod('div');
	o.innerHTML = (
		'<div id="drops">\n' +
		'	<div class="dropdesc" id="up_zd"><div>🚀 ' + L.udt_up + '<br /><span></span><div>🚀<b>' + L.udt_up + '</b></div><div><b>' + L.udt_up + '</b>🚀</div></div></div>\n' +
		'	<div class="dropdesc" id="srch_zd"><div>🔎 ' + L.udt_srch + '<br /><span></span><div>🔎<b>' + L.udt_srch + '</b></div><div><b>' + L.udt_srch + '</b>🔎</div></div></div>\n' +
		'	<div class="dropzone" id="up_dz" v="up_zd"></div>\n' +
		'	<div class="dropzone" id="srch_dz" v="srch_zd"></div>\n' +
		'</div>'
	);
	document.body.appendChild(o);
})();


// config panel
ebi('op_cfg').innerHTML = (
	'<div>\n' +
	'	<h3>' + L.cl_opts + '</h3>\n' +
	'	<div>\n' +
	'		<a id="tooltips" class="tgl btn" href="#" tt="' + L.ct_ttips + '</a>\n' +
	'		<a id="griden" class="tgl btn" href="#" tt="' + L.wt_grid + '">' + L.ct_grid + '</a>\n' +
	'		<a id="thumbs" class="tgl btn" href="#" tt="' + L.ct_thumb + '</a>\n' +
	'		<a id="csel" class="tgl btn" href="#" tt="' + L.ct_csel + '</a>\n' +
	'		<a id="ihop" class="tgl btn" href="#" tt="' + L.ct_ihop + '</a>\n' +
	'		<a id="dotfiles" class="tgl btn" href="#" tt="' + L.ct_dots + '</a>\n' +
	'		<a id="qdel" class="tgl btn" href="#" tt="' + L.ct_qdel + '</a>\n' +
	'		<a id="dir1st" class="tgl btn" href="#" tt="' + L.ct_dir1st + '</a>\n' +
	'		<a id="nsort" class="tgl btn" href="#" tt="' + L.ct_nsort + '</a>\n' +
	'		<a id="utctid" class="tgl btn" href="#" tt="' + L.ct_utc + '</a>\n' +
	'		<a id="ireadme" class="tgl btn" href="#" tt="' + L.ct_readme + '</a>\n' +
	'		<a id="idxh" class="tgl btn" href="#" tt="' + L.ct_idxh + '</a>\n' +
	'		<a id="sbars" class="tgl btn" href="#" tt="' + L.ct_sbars + '</a>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_hfsz + '</h3>\n' +
	'	<div><select id="fszfmt">\n' +
	'		<option value="0">0 ┃ 1234567</option>\n' +
	'		<option value="1">1 ┃ 1 234 567</option>\n' +
	'		<option value="2">2- ┃ 1.18 M</option>\n' +
	'		<option value="2c">2c ┃ 1.18 M</option>\n' +
	'		<option value="3">3- ┃ 1.2 M</option>\n' +
	'		<option value="3c">3c ┃ 1.2 M</option>\n' +
	'		<option value="4">4- ┃ 1.18 MB</option>\n' +
	'		<option value="4c">4c ┃ 1.18 MB</option>\n' +
	'		<option value="5">5- ┃ 1.2 MB</option>\n' +
	'		<option value="5c">5c ┃ 1.2 MB</option>\n' +
	'		<option value="fuzzy">fuzzy</option>\n' +
	'	</select></div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_themes + '</h3>\n' +
	'	<div><select id="themes"></select></div>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_langs + '</h3>\n' +
	'	<div><select id="langs"></select></div>\n' +
	'</div>\n' +
	(have_zip ? (
		'<div><h3>' + L.cl_ziptype + '</h3><div id="arc_fmt"></div></div>\n'
	) : '') +
	'<div>\n' +
	'	<h3>' + L.cl_uopts + '</h3>\n' +
	'	<div>\n' +
	'		<a id="ask_up" class="tgl btn" href="#" tt="' + L.ut_ask + '</a>\n' +
	'		<a id="u2ts" class="tgl btn" href="#" tt="' + L.ut_u2ts + '</a>\n' +
	'		<a id="umod" class="tgl btn" href="#" tt="' + L.cut_umod + '</a>\n' +
	'		<a id="hashw" class="tgl btn" href="#" tt="' + L.cut_mt + '</a>\n' +
	'		<a id="nosubtle" class="tgl btn" href="#" tt="' + L.cut_wasm + '</a>\n' +
	'		<a id="u2turbo" class="tgl btn ttb" href="#" tt="' + L.cut_turbo + '</a>\n' +
	'		<a id="u2tdate" class="tgl btn ttb" href="#" tt="' + L.cut_datechk + '</a>\n' +
	'		<input type="text" id="u2szg" value="" ' + NOAC + ' style="width:3em" tt="' + L.cut_u2sz + '" />' +
	'		<a id="flag_en" class="tgl btn" href="#" tt="' + L.cut_flag + '">💤</a>\n' +
	'		<a id="u2sort" class="tgl btn" href="#" tt="' + L.cut_az + '">az</a>\n' +
	'		<a id="upnag" class="tgl btn" href="#" tt="' + L.cut_nag + '">🔔</a>\n' +
	'		<a id="upsfx" class="tgl btn" href="#" tt="' + L.cut_sfx + '">🔊</a>\n' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_favico + ' <span id="ico1">🎉</span></h3>\n' +
	'	<div>\n' +
	'		<input type="text" id="icot" value="" ' + NOAC + ' style="width:1.3em" tt="' + L.cft_text + '" />' +
	'		<input type="text" id="icof" value="" ' + NOAC + ' style="width:2em" tt="' + L.cft_fg + '" />' +
	'		<input type="text" id="icob" value="" ' + NOAC + ' style="width:2em" tt="' + L.cft_bg + '" />' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_bigdir + '</h3>\n' +
	'	<div>\n' +
	'		<input type="text" id="bd_lim" value="250" ' + NOAC + ' style="width:4em" tt="' + L.cdt_lim + '" />' +
	'		<a id="bd_ask" class="tgl btn" href="#" tt="' + L.cdt_ask + '">ask</a>\n' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_hsort + '</h3>\n' +
	'	<div>\n' +
	'		<input type="text" id="hsortn" value="" ' + NOAC + ' style="width:3em" tt="' + L.cdt_hsort + '" />' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div><h3>' + L.cl_keytype + '</h3><div><select id="key_notation"></select></div></div>\n' +
	'<div><h3>' + L.cl_hiddenc + ' &nbsp;' + (MOBILE ? '<a href="#" id="hcolsh">' + L.cl_hidec + '</a> / ' : '') + '<a href="#" id="hcolsr">' + L.cl_reset + '</a></h3><div id="hcols"></div></div>'
);


// navpane
ebi('tree').innerHTML = (
	'<div id="treeh">\n' +
	'	<a href="#" id="detree" tt="' + L.tt_detree + '">🍞...</a>\n' +
	'	<a href="#" class="btn" step="2" id="twobytwo" tt="Hotkey: D">+</a>\n' +
	'	<a href="#" class="btn" step="-2" id="twig" tt="Hotkey: A">&ndash;</a>\n' +
	'	<a href="#" class="btn" id="visdir" tt="' + L.tt_visdir + '">🎯</a>\n' +
	'	<a href="#" class="tgl btn" id="filetree" tt="' + L.tt_ftree + '">📃</a>\n' +
	'	<a href="#" class="tgl btn" id="parpane" tt="' + L.tt_pdock + '">📌</a>\n' +
	'	<a href="#" class="tgl btn" id="dyntree" tt="' + L.tt_dynt + '">a</a>\n' +
	'	<a href="#" class="tgl btn" id="wraptree" tt="' + L.tt_wrap + '">↵</a>\n' +
	'	<a href="#" class="tgl btn" id="hovertree" tt="' + L.tt_hover + '">👀</a>\n' +
	'</div>\n' +
	'<ul id="docul"></ul>\n' +
	'<ul class="ntree" id="treepar"></ul>\n' +
	'<ul class="ntree" id="treeul"></ul>\n' +
	'<div id="thx_ff">&nbsp;</div>'
);
clmod(ebi('tree'), 'sbar', 1);
ebi('entree').setAttribute('tt', L.tt_entree);
ebi('goh').textContent = L.goh;
QS('#op_mkdir input[type="submit"]').value = L.ab_mkdir;
QS('#op_new_md input[type="submit"]').value = L.ab_mkdoc;
QS('#op_msg input[type="submit"]').value = L.ab_msg;


(function () {
	var ops = QSA('#ops>a');
	for (var a = 0; a < ops.length; a++) {
		ops[a].onclick = opclick;
		var v = ops[a].getAttribute('data-dest');
		if (v)
			ops[a].href = '#v=' + v;
	}
})();


function opclick(e) {
	var dest = this.getAttribute('data-dest');
	if (QS('#op_' + dest + '.act'))
		dest = '';

	swrite('opmode', dest || null);
	if (ctrl(e))
		return;

	ev(e);
	goto(dest);

	var input = QS('.opview.act input:not([type="hidden"])')
	if (input && !TOUCH) {
		tt.skip = true;
		input.focus();
	}
}


function goto(dest) {
	var obj = QSA('.opview.act');
	for (var a = obj.length - 1; a >= 0; a--)
		clmod(obj[a], 'act');

	obj = QSA('#ops>a');
	for (var a = obj.length - 1; a >= 0; a--)
		clmod(obj[a], 'act');

	if (dest) {
		var lnk = QS('#ops>a[data-dest=' + dest + ']'),
			nps = lnk.getAttribute('data-perm');

		nps = nps && nps.length ? nps.split(' ') : [];

		if (perms.length)
			for (var a = 0; a < nps.length; a++)
				if (!has(perms, nps[a]))
					return;

		if (!has(perms, 'read') && !has(perms, 'write') && (dest == 'up2k'))
			return;

		clmod(ebi('op_' + dest), 'act', 1);
		clmod(lnk, 'act', 1);

		var fn = window['goto_' + dest];
		if (fn)
			fn();
	}

	clmod(document.documentElement, 'op_open', dest);

	if (treectl)
		treectl.onscroll();
}


var m = SPINNER.split(','),
	SPINNER_CSS = SPINNER.slice(1 + m[0].length);
SPINNER = m[0];


var SBW, SBH;  // scrollbar size
function read_sbw() {
	var el = mknod('div');
	el.style.cssText = 'overflow:scroll;width:100px;height:100px;position:absolute;top:0;left:0';
	document.body.appendChild(el);
	SBW = el.offsetWidth - el.clientWidth;
	SBH = el.offsetHeight - el.clientHeight;
	document.body.removeChild(el);
	setcvar('--sbw', SBW + 'px');
	setcvar('--sbh', SBH + 'px');
}
onresize100.add(read_sbw, true);


var have_webp = sread('have_webp');
(function () {
	if (have_webp !== null)
		return;

	var img = new Image();
	img.onload = function () {
		have_webp = img.width > 0 && img.height > 0;
		swrite('have_webp', 'ya');
	};
	img.onerror = function () {
		have_webp = false;
		swrite('have_webp', '');
	};
	img.src = "data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==";
})();


function set_files_html(html) {
	var files = ebi('files');
	try {
		files.innerHTML = html;
		return files;
	}
	catch (e) {
		var par = files.parentNode;
		par.removeChild(files);
		files = mknod('div');
		files.innerHTML = '<table id="files">' + html + '</table>';
		par.insertBefore(files.childNodes[0], ebi('lazy'));
		files = ebi('files');
		return files;
	}
}


// actx breaks background album playback on ios
var ACtx = !IPHONE && (window.AudioContext || window.webkitAudioContext),
	ACB = sread('au_cbv') || 1,
	hash0 = location.hash,
	sloc0 = '' + location,
	noih = /[?&]v\b/.exec(sloc0),
	dbg_kbd = /[?&]dbgkbd\b/.exec(sloc0),
	abrt_key = "",
	can_shr = false,
	rtt = null,
	srvinf = "",
	ldks = [],
	dks = {},
	dk, mp;


if (location.pathname.indexOf('//') === 0)
	hist_replace(location.pathname.replace(/^\/+/, '/'));


if (window.og_fn) {
	hash0 = 1;
	hist_replace(vsplit(get_evpath())[0]);
}


var hsortn = ebi('hsortn').value = icfg_get('hsortn', dhsortn);
ebi('hsortn').oninput = function (e) {
	var n = parseInt(this.value);
	swrite('hsortn', hsortn = (isNum(n) ? n : dhsortn));
};
(function() {
	var args = ('' + hash0).split(/,sort/g);
	if (args.length < 2)
		return;

	var ret = [];
	for (var a = 1; a < args.length; a++) {
		var t = '', n = 1, z = args[a].split(',')[0];
		if (z.startsWith('-')) {
			z = z.slice(1);
			n = -1;
		}
		if (z == "sz" || z.indexOf('/.') + 1)
			t = "int";
		ret.push([z, n, t]);
	}
	n = Math.min(ret.length, hsortn);
	if (n) {
		var cmp = jread('fsort', []);
		if (JSON.stringify(ret.slice(0, n) !=
			JSON.stringify(cmp.slice(0, n))))
			jwrite('fsort', ret);
	}
})();


var mpl = (function () {
	var have_mctl = 'mediaSession' in navigator && window.MediaMetadata;

	ebi('op_player').innerHTML = (
		'<div><h3>' + L.cl_opts + '</h3><div>' +
		'<a href="#" class="tgl btn" id="au_loop" tt="' + L.mt_loop + '</a>' +
		'<a href="#" class="tgl btn" id="au_one" tt="' + L.mt_one + '</a>' +
		'<a href="#" class="tgl btn" id="au_shuf" tt="' + L.mt_shuf + '</a>' +
		'<a href="#" class="tgl btn" id="au_aplay" tt="' + L.mt_aplay + '</a>' +
		'<a href="#" class="tgl btn" id="au_preload" tt="' + L.mt_preload + '</a>' +
		'<a href="#" class="tgl btn" id="au_prescan" tt="' + L.mt_prescan + '</a>' +
		'<a href="#" class="tgl btn" id="au_fullpre" tt="' + L.mt_fullpre + '</a>' +
		'<a href="#" class="tgl btn" id="au_fau" tt="' + L.mt_fau + '</a>' +
		'<a href="#" class="tgl btn" id="au_waves" tt="' + L.mt_waves + '</a>' +
		'<a href="#" class="tgl btn" id="au_npclip" tt="' + L.mt_npclip + '</a>' +
		'<a href="#" class="tgl btn" id="au_m3u_c" tt="' + L.mt_m3u_c + '</a>' +
		'<a href="#" class="tgl btn" id="au_os_ctl" tt="' + L.mt_octl + '</a>' +
		'<a href="#" class="tgl btn" id="au_os_seek" tt="' + L.mt_oseek + '</a>' +
		'<a href="#" class="tgl btn" id="au_osd_cv" tt="' + L.mt_oscv + '</a>' +
		'<a href="#" class="tgl btn" id="au_follow" tt="' + L.mt_follow + '</a>' +
		'<a href="#" class="tgl btn" id="au_compact" tt="' + L.mt_compact + '</a>' +
		'</div></div>' +

		'<div><h3>' + L.ml_btns + '</h3><div>' +
		'<a href="#" class="btn" id="au_uncache" tt="' + L.mt_uncache + '</a>' +
		'</div></div>' +

		'<div><h3>' + L.ml_pmode + '</h3><div id="pb_mode">' +
		'<a href="#" class="tgl btn" m="loop" tt="' + L.mt_mloop + '</a>' +
		'<a href="#" class="tgl btn" m="next" tt="' + L.mt_mnext + '</a>' +
		'<a href="#" class="tgl btn" m="stop" tt="' + L.mt_mstop + '</a>' +
		'</div></div>' +

		(have_acode ? (
			'<div><h3>' + L.ml_tcode + '</h3><div>' +
			'<a href="#" id="ac_flac" class="tgl btn" tt="' + L.mt_cflac + '</a>' +
			'<a href="#" id="ac_aac" class="tgl btn" tt="' + L.mt_caac + '</a>' +
			'<a href="#" id="ac_oth" class="tgl btn" tt="' + L.mt_coth + '</a>' +
			'</div></div>' +
			'<div><h3>' + L.ml_tcode2 + '</h3><div>' +
			'<a href="#" id="ac2opus" class="tgl btn" tt="' + L.mt_c2opus + '</a>' +
			'<a href="#" id="ac2owa" class="tgl btn" tt="' + L.mt_c2owa + '</a>' +
			'<a href="#" id="ac2caf" class="tgl btn" tt="' + L.mt_c2caf + '</a>' +
			'<a href="#" id="ac2mp3" class="tgl btn" tt="' + L.mt_c2mp3 + '</a>' +
			'<a href="#" id="ac2flac" class="tgl btn" tt="' + L.mt_c2flac + '</a>' +
			'<a href="#" id="ac2wav" class="tgl btn" tt="' + L.mt_c2wav + '</a>' +
			'</div></div>'
		) : '') +

		'<div><h3>' + L.ml_tint + '</h3><div>' +
		'<input type="text" id="pb_tint" value="0" ' + NOAC + ' style="width:2.4em" tt="' + L.mt_tint + '" />' +
		'</div></div>' +

		'<div><h3 id="h_drc">' + L.ml_drc + '</h3><div id="audio_drc"></div></div>' +
		'<div><h3>' + L.ml_eq + '</h3><div id="audio_eq"></div></div>' +
		'');

	var r = {
		"pb_mode": (sread('pb_mode', ['loop', 'next', 'stop']) || 'next').split('-')[0],
		"os_ctl": bcfg_get('au_os_ctl', have_mctl) && have_mctl,
		'traversals': 0,
		'm3ut': '#EXTM3U\n',
	};
	bcfg_bind(r, 'one', 'au_one', false, function (v) {
		if (mp.au)
			mp.au.loop = !v && r.loop;
	});
	bcfg_bind(r, 'loop', 'au_loop', false, function (v) {
		if (mp.au)
			mp.au.loop = v;
	});
	bcfg_bind(r, 'shuf', 'au_shuf', false, function () {
		mp.read_order();  // don't bind
	});
	bcfg_bind(r, 'aplay', 'au_aplay', true);
	bcfg_bind(r, 'preload', 'au_preload', true);
	bcfg_bind(r, 'prescan', 'au_prescan', true);
	bcfg_bind(r, 'fullpre', 'au_fullpre', false);
	bcfg_bind(r, 'fau', 'au_fau', MOBILE && !IPHONE, function (v) {
		mp.nopause();
		if (mp.fau) {
			mp.fau.pause();
			mp.fau = mpo.fau = null;
			console.log('stop fau');
		}
		mp.init_fau();
	});
	bcfg_bind(r, 'waves', 'au_waves', true, function (v) {
		if (!v) pbar.unwave();
	});
	bcfg_bind(r, 'os_seek', 'au_os_seek', !IPHONE, announce);
	bcfg_bind(r, 'osd_cv', 'au_osd_cv', true, announce);
	bcfg_bind(r, 'clip', 'au_npclip', false, function (v) {
		clmod(ebi('wtoggle'), 'np', v && mp.au);
	});
	bcfg_bind(r, 'm3uen', 'au_m3u_c', false, function (v) {
		clmod(ebi('wtoggle'), 'm3u', v && (mp.au || msel.getsel().length));
	});
	bcfg_bind(r, 'follow', 'au_follow', false, setaufollow);
	bcfg_bind(r, 'ac_flac', 'ac_flac', true);
	bcfg_bind(r, 'ac_aac', 'ac_aac', false);
	bcfg_bind(r, 'ac_oth', 'ac_oth', true, reload_mp);
	if (!have_acode)
		r.ac_flac = r.ac_aac = r.ac_oth = false;

	if (IPHONE) {
		ebi('au_fullpre').style.display = 'none';
		r.fullpre = false;
	}

	ebi('au_uncache').onclick = function (e) {
		ev(e);
		ACB = (Date.now() % 46656).toString(36);
		swrite('au_cbv', ACB);
		reload_mp();
		toast.inf(5, L.mm_uncache);
	};

	ebi('au_os_ctl').onclick = function (e) {
		ev(e);
		r.os_ctl = !r.os_ctl && have_mctl;
		bcfg_set('au_os_ctl', r.os_ctl);
		if (!have_mctl)
			toast.err(5, L.mp_breq);
	};

	function draw_pb_mode() {
		var btns = QSA('#pb_mode>a');
		for (var a = 0, aa = btns.length; a < aa; a++) {
			clmod(btns[a], 'on', btns[a].getAttribute("m") == r.pb_mode);
			btns[a].onclick = set_pb_mode;
		}
	}
	draw_pb_mode();

	function set_pb_mode(e) {
		ev(e);
		r.pb_mode = this.getAttribute('m');
		swrite('pb_mode', r.pb_mode);
		draw_pb_mode();
	}

	function set_tint() {
		var tint = icfg_get('pb_tint', 0);
		if (!tint)
			ebi('barbuf').style.removeProperty('background');
		else
			ebi('barbuf').style.background = 'rgba(126,163,75,' + (tint / 100.0) + ')';
	}
	ebi('pb_tint').oninput = function (e) {
		swrite('pb_tint', this.value);
		set_tint();
	};
	set_tint();

	r.acode = function (url) {
		var c = true,
			cs = url.split('?')[0];

		if (!have_acode)
			c = false;
		else if (/\.(wav|flac)$/i.exec(cs))
			c = r.ac_flac;
		else if (/\.(aac|m4a)$/i.exec(cs))
			c = r.ac_aac;
		else if (/\.(oga|ogg|opus)$/i.exec(cs) && (!can_ogg || mpl.ac2 == 'mp3'))
			c = true;
		else if (re_au_native.exec(cs))
			c = false;

		// allow flac->flac (bitstream fixup)
		if (!c)
			return url;

		return addq(url, 'th=' + r.ac2);
	};

	r.set_ac2 = function () {
		r.init_ac2(this.getAttribute('id').split('ac2')[1]);
	};

	r.init_ac2 = function (v) {
		if (!window.have_acode) {
			r.ac2 = 'opus';
			return;
		}

		var dv = can_ogg ? 'opus' :
				can_caf ? 'caf' : 'mp3',
			fmts = ['opus', 'owa', 'caf', 'mp3', 'flac', 'wav'],
			btns = [];

		if (v === dv)
			toast.ok(5, L.mt_c2ok);
		else if (v)
			toast.inf(10, L.mt_c2nd);

		if ((v == 'opus' && !can_ogg) ||
			(v == 'caf' && !can_caf) ||
			(v == 'owa' && !can_owa) ||
			(v == 'flac' && !can_flac))
			toast.warn(15, L.mt_c2ng);

		if (v == 'owa' && IPHONE)
			toast.err(30, L.mt_xowa);

		for (var a = 0; a < fmts.length; a++) {
			var btn = ebi('ac2' + fmts[a]);
			if (!btn)
				return console.log('!btn', fmts[a]);
			btn.onclick = r.set_ac2;
			btns.push(btn);
		}
		if (!IPHONE)
			btns[1].style.display = btns[2].style.display = 'none';
		btns[4].style.display = have_c2flac ? '' : 'none';
		btns[5].style.display = have_c2wav ? '' : 'none';

		if (v)
			swrite('acode2', v);
		else
			v = dv;

		v = sread('acode2', fmts) || v;
		for (var a = 0; a < fmts.length; a++)
			clmod(btns[a], 'on', fmts[a] == v)

		r.ac2 = v;
		ebi('ac_flac').setAttribute('tt', L.mt_cflac.split('"')[0].format(v));
		ebi('ac_aac').setAttribute('tt', L.mt_caac.split('"')[0].format(v));
		ebi('ac_oth').setAttribute('tt', L.mt_coth.split('"')[0].format(v));
	};

	r.pp = function () {
		var adur, apos, playing = mp.au && !mp.au.paused;

		clearTimeout(mpl.t_eplay);

		clmod(ebi('np_inf'), 'playing', playing);

		if (mp.au && isNum(adur = mp.au.duration) && isNum(apos = mp.au.currentTime) && apos >= 0)
			ebi('np_pos').textContent = s2ms(apos);

		if (!r.os_ctl)
			return;

		navigator.mediaSession.playbackState = playing ? "playing" : "paused";
	};

	function setaufollow() {
		window[(r.follow ? "add" : "remove") + "EventListener"]("resize", scroll2playing);
	}
	setaufollow();

	function announce() {
		if (!r.os_ctl || !mp.au)
			return;

		var np = get_np()[0],
			fns = np.file.split(' - '),
			artist = (np.circle && np.circle != np.artist ? np.circle + ' // ' : '') + (np.artist || (fns.length > 1 ? fns[0] : '')),
			title = np.title || fns.pop(),
			cover = '',
			tags = { title: title };

		if (artist)
			tags.artist = artist;

		if (np.album)
			tags.album = np.album;

		if (r.osd_cv) {
			var files = QSA("#files tr>td:nth-child(2)>a[id]"),
				cover = null;

			for (var a = 0, aa = files.length; a < aa; a++) {
				if (/^(cover|folder)\.(jpe?g|png|gif)$/i.test(files[a].textContent)) {
					cover = files[a].getAttribute('href');
					break;
				}
			}

			if (cover) {
				cover = addq(cover, 'th=j');
				tags.artwork = [{ "src": cover, type: "image/jpeg" }];
			}
		}

		ebi('np_circle').textContent = np.circle || '';
		ebi('np_album').textContent = np.album || '';
		ebi('np_tn').textContent = np['.tn'] || '';
		ebi('np_artist').textContent = np.artist || (fns.length > 1 ? fns[0] : '');
		ebi('np_title').textContent = np.title || '';
		ebi('np_dur').textContent = np['.dur'] || '';
		ebi('np_url').textContent = uricom_dec(get_evpath()) + np.file.split('?')[0];
		if (!MOBILE && cover)
			ebi('np_img').setAttribute('src', cover);
		else
			ebi('np_img').removeAttribute('src');

		navigator.mediaSession.metadata = new MediaMetadata(tags);
		navigator.mediaSession.setActionHandler('play', mplay);
		navigator.mediaSession.setActionHandler('pause', mpause);
		navigator.mediaSession.setActionHandler('seekbackward', r.os_seek ? function () { seek_au_rel(-10); } : null);
		navigator.mediaSession.setActionHandler('seekforward', r.os_seek ? function () { seek_au_rel(10); } : null);
		navigator.mediaSession.setActionHandler('previoustrack', prev_song);
		navigator.mediaSession.setActionHandler('nexttrack', next_song);
		r.pp();
	}
	r.announce = announce;

	r.stop = function () {
		if (!r.os_ctl)
			return;

		// dead code; left for debug
		navigator.mediaSession.metadata = null;
		navigator.mediaSession.playbackState = "paused";

		var hs = 'play pause seekbackward seekforward previoustrack nexttrack'.split(/ /g);
		for (var a = 0; a < hs.length; a++)
			navigator.mediaSession.setActionHandler(hs[a], null);

		navigator.mediaSession.setPositionState();
	};

	r.unbuffer = function (url) {
		if (mp.au2 && (!url || mp.au2.rsrc == url)) {
			mp.au2.src = mp.au2.rsrc = '';
			mp.au2.ld = 0; //owa
			mp.au2.load();
		}
		if (!url)
			mpl.preload_url = null;
	}

	return r;
})();


var za,
	can_ogg = true,
	can_owa = false,
	can_flac = false,
	can_caf = APPLE && !/ OS ([1-9]|1[01])_/.test(UA);
try {
	za = new Audio();
	can_ogg = za.canPlayType('audio/ogg; codecs=opus') === 'probably';
	can_owa = za.canPlayType('audio/webm; codecs=opus') === 'probably';
	can_flac = za.canPlayType('audio/flac') === 'probably';
	can_caf = za.canPlayType('audio/x-caf') && can_caf; //'maybe'
}
catch (ex) { }
za = null;

if (can_owa && APPLE && / OS ([1-9]|1[0-7])_/.test(UA))
	can_owa = false;

mpl.init_ac2();


var re_m3u = /\.(m3u8?)$/i;
var re_au_native = (can_ogg || have_acode) ? /\.(aac|flac|m4a|mp3|oga|ogg|opus|wav)$/i : /\.(aac|flac|m4a|mp3|wav)$/i,
	re_au_vid = /\.(3gp|asf|avi|flv|m4v|mkv|mov|mp4|mpeg|mpeg2|mpegts|mpg|mpg2|nut|ogm|ogv|rm|ts|vob|webm|wmv)$/i,
	re_au_all = /\.(aac|ac3|aif|aiff|alac|alaw|amr|ape|au|dfpwm|dts|flac|gsm|it|itgz|itxz|itz|m4a|mdgz|mdxz|mdz|mo3|mod|mp2|mp3|mpc|mptm|mt2|mulaw|oga|ogg|okt|opus|ra|s3m|s3gz|s3xz|s3z|tak|tta|ulaw|wav|wma|wv|xm|xmgz|xmxz|xmz|xpk|3gp|asf|avi|flv|m4v|mkv|mov|mp4|mpeg|mpeg2|mpegts|mpg|mpg2|nut|ogm|ogv|rm|ts|vob|webm|wmv)$/i;


// extract songs + add play column
var mpo = { "au": null, "au2": null, "acs": null, "fau": null };
function MPlayer() {
	var r = this;
	r.id = Date.now();
	r.au = mpo.au;
	r.au2 = mpo.au2;
	r.acs = mpo.acs;
	r.fau = mpo.fau;
	r.tracks = {};
	r.order = [];
	r.cd_pause = 0;

	var re_audio = have_acode && mpl.ac_oth ? re_au_all : re_au_native,
		trs = QSA('#files tbody tr');

	for (var a = 0, aa = trs.length; a < aa; a++) {
		var tds = trs[a].getElementsByTagName('td'),
			link = tds[1].getElementsByTagName('a');

		link = link[link.length - 1];
		var url = link.getAttribute('href'),
			fn = url.split('?')[0];

		if (re_audio.exec(fn)) {
			var tid = link.getAttribute('id'),
				txt = re_au_vid.exec(fn) ? '(🎧)' : L.mb_play;
			r.order.push(tid);
			r.tracks[tid] = url;
			tds[0].innerHTML = '<a id="a' + tid + '" href="#a' + tid + '" class="play">' + txt + '</a></td>';
			ebi('a' + tid).onclick = ev_play;
			clmod(trs[a], 'au', 1);
		}
		else if (re_m3u.exec(fn)) {
			var tid = link.getAttribute('id');
			tds[0].innerHTML = '<a id="a' + tid + '" href="#a' + tid + '" class="play">' + L.mb_play + '</a></td>';
			ebi('a' + tid).onclick = ev_load_m3u;
		}
	}

	r.vol = clamp(fcfg_get('vol', IPHONE ? 1 : dvol / 100), 0, 1);

	r.expvol = function (v) {
		return 0.5 * v + 0.5 * v * v;
	};

	r.setvol = function (vol) {
		r.vol = clamp(vol, 0, 1);
		swrite('vol', vol);
		r.stopfade(true);

		if (r.au)
			r.au.volume = r.expvol(r.vol);
	};

	r.shuffle = function () {
		if (!mpl.shuf)
			return;

		// durstenfeld
		for (var a = r.order.length - 1; a > 0; a--) {
			var b = Math.floor(Math.random() * (a + 1)),
				c = r.order[a];
			r.order[a] = r.order[b];
			r.order[b] = c;
		}
	};
	r.shuffle();

	r.read_order = function () {
		var order = [],
			links = QSA('#files>tbody>tr>td:nth-child(1)>a');

		for (var a = 0, aa = links.length; a < aa; a++) {
			var tid = links[a].getAttribute('id');
			if (!tid || tid.indexOf('af-') !== 0)
				continue;

			order.push(tid.slice(1));
		}
		r.order = order;
		r.shuffle();
	};

	r.fdir = 0;
	r.fvol = -1;
	r.ftid = -1;
	r.ftimer = null;
	r.fade_in = function () {
		r.nopause();
		r.fvol = 0;
		r.fdir = 0.025 * r.vol * (CHROME ? 1.5 : 1);
		if (r.au) {
			r.ftid = r.au.tid;
			r.au.play();
			mpl.pp();
			fader();
		}
	};
	r.fade_out = function () {
		r.fvol = r.vol;
		r.fdir = -0.05 * r.vol * (CHROME ? 2 : 1);
		r.ftid = r.au.tid;
		fader();
	};
	r.stopfade = function (hard) {
		clearTimeout(r.ftimer);
		if (hard)
			r.ftid = -1;
	}
	function fader() {
		r.stopfade();
		if (!r.au || r.au.tid !== r.ftid)
			return;

		var done = true;
		r.fvol += r.fdir / (r.fdir < 0 && r.fvol < r.vol / 4 ? 2 : 1);
		if (r.fvol < 0) {
			r.fvol = 0;
			r.au.pause();
			mpl.pp();

			var t = r.au.currentTime - 0.8;
			if (isNum(t))
				r.au.currentTime = Math.max(t, 0);
		}
		else if (r.fvol > r.vol)
			r.fvol = r.vol;
		else
			done = false;

		r.au.volume = r.expvol(r.fvol);
		if (!done)
			setTimeout(fader, 10);
	}

	r.preload = function (url, full) {
		var t0 = Date.now(),
			fname = uricom_dec(url.split('/').pop().split('?')[0]);

		url = addq(mpl.acode(url), 'cache=987&_=' + ACB);
		mpl.preload_url = full ? url : null;

		if (mpl.waves)
			fetch(url.replace(/\bth=(opus|mp3)&/, '') + '&th=p').then(function (x) {
				x.body.getReader().read();
			});

		if (full)
			return fetch(url).then(function (x) {
				var rd = x.body.getReader(), n = 0;
				function spd() {
					return humansize(n / ((Date.now() + 1 - t0) / 1000)) + '/s';
				}
				function drop(x) {
					if (x && x.done)
						return console.log('xhr-preload finished, ' + spd());

					if (x && x.value && x.value.length)
						n += x.value.length;

					if (mpl.preload_url !== url || n >= 128 * 1024 * 1024) {
						console.log('xhr-preload aborted at ' + Math.floor(n / 1024) + ' KiB, ' + spd() + ' for ' + url);
						return rd.cancel();
					}

					return rd.read().then(drop);
				}
				drop();
			});

		r.nopause();
		r.au2.ld = 0; //owa
		r.au2.onloadeddata = r.au2.onloadedmetadata = r.onpreload;
		r.au2.preload = "auto";
		r.au2.src = r.au2.rsrc = url;

		if (mpl.prescan_evp) {
			mpl.prescan_evp = null;
			toast.ok(7, L.mm_scank + "\n" + esc(fname));
		}
		console.log("preloading " + fname);
	};

	r.nopause = function () {
		r.cd_pause = Date.now();
	};

	r.onpreload = function () {
		r.nopause();
		this.ld++;
	};

	r.init_fau = function () {
		if (r.fau || !mpl.fau)
			return;

		// breaks touchbar-macs
		console.log('init fau');
		r.fau = new Audio(SR + '/.cpr/deps/busy.mp3?_=' + TS);
		r.fau.loop = true;
		r.fau.play();
	};

	r.set_ev = function () {
		mp.au.onended = evau_end;
		mp.au.onerror = evau_error;
		mp.au.onprogress = pbar.drawpos;
		mp.au.onplaying = mpui.progress_updater;
		mp.au.onloadeddata = mp.au.onloadedmetadata = mp.nopause;
	};
}


function ft2dict(tr, skip) {
	var th = ebi('files').tHead.rows[0].cells,
		rv = [],
		rh = [],
		ra = [],
		rt = {};

	skip = skip || {};

	for (var a = 1, aa = th.length; a < aa; a++) {
		var tv = tr.cells[a].textContent,
			tk = a == 1 ? 'file' : th[a].getAttribute('name').split('/').pop().toLowerCase(),
			vis = th[a].className.indexOf('min') === -1;

		if (!tv || skip[tk])
			continue;

		(vis ? rv : rh).push(tk);
		ra.push(tk);
		rt[tk] = tv;
	}
	return [rt, rv, rh, ra];
}


function get_np() {
	var tr = QS('#files tr.play');
	return ft2dict(tr, { 'up_ip': 1 });
};


// toggle player widget
var widget = (function () {
	var r = {},
		widget = ebi('widget'),
		wtico = ebi('wtico'),
		nptxt = ebi('nptxt'),
		npirc = ebi('npirc'),
		m3ua = ebi('m3ua'),
		m3uc = ebi('m3uc'),
		touchmode = false,
		was_paused = true;

	r.open = function () {
		return r.set(true);
	};
	r.close = function () {
		return r.set(false);
	};
	r.set = function (is_open) {
		if (r.is_open == is_open)
			return false;

		clmod(document.documentElement, 'np_open', is_open);
		clmod(widget, 'open', is_open);
		bcfg_set('au_open', r.is_open = is_open);
		if (vbar) {
			pbar.onresize();
			vbar.onresize();
		}
		return true;
	};
	r.toggle = function (e) {
		r.open() || r.close();
		ev(e);
		return false;
	};
	r.paused = function (paused) {
		if (was_paused != paused) {
			was_paused = paused;
			ebi('bplay').innerHTML = paused ? '▶' : '⏸';
		}
	};
	r.setvis = function () {
		widget.style.display = !has(perms, "read") || showfile.abrt ? 'none' : '';
	};
	wtico.onclick = function (e) {
		if (!touchmode)
			r.toggle(e);

		return false;
	};
	npirc.onclick = nptxt.onclick = function (e) {
		ev(e);
		var irc = this.getAttribute('id') == 'npirc',
			ck = irc ? '06' : '',
			cv = irc ? '07' : '',
			m = ck + 'np: ',
			npr = get_np(),
			npk = npr[1],
			np = npr[0];

		for (var a = 0; a < npk.length; a++)
			m += (npk[a] == 'file' ? '' : npk[a]).replace(/^\./, '') + '(' + cv + np[npk[a]] + ck + ') // ';

		m += '[' + cv + s2ms(mp.au.currentTime) + ck + '/' + cv + s2ms(mp.au.duration) + ck + ']';

		cliptxt(m, function () {
			toast.ok(1, L.clipped, null, 'top');
		});
	};
	m3ua.onclick = function (e) {
		ev(e);
		var el,
			files = [],
			sel = msel.getsel();

		for (var a = 0; a < sel.length; a++) {
			el = ebi(sel[a].id).closest('tr');
			if (clgot(el, 'au'))
				files.push(el);
		}
		el = QS('#files tr.play');
		if (!sel.length && el)
			files.push(el);

		for (var a = 0; a < files.length; a++) {
			var md = ft2dict(files[a])[0],
				dur = md['.dur'] || '1',
				tag = '';

			if (md.artist && md.title)
				tag = md.artist + ' - ' + md.title;
			else if (md.artist)
				tag = md.artist + ' - ' + md.file;
			else if (md.title)
				tag = md.title;

			if (dur.indexOf(':') > 0) {
				dur = dur.split(':');
				dur = 60 * parseInt(dur[0]) + parseInt(dur[1]);
			}
			else dur = parseInt(dur);

			mpl.m3ut += '#EXTINF:' + dur + ',' + tag + '\n' + uricom_dec(get_evpath()) + md.file + '\n';
		}
		toast.ok(2, files.length == 1 ? L.m3u_add1 : L.m3u_addn.format(files.length), null, 'top');
	};
	m3uc.onclick = function (e) {
		ev(e);
		cliptxt(mpl.m3ut, function () {
			toast.ok(15, L.m3u_clip, null, 'top');
		});
	};
	r.set(sread('au_open') == 1);
	setTimeout(function () {
		clmod(widget, 'anim', 1);
	}, 10);
	return r;
})();


function canvas_cfg(can) {
	var r = {},
		b = can.getBoundingClientRect(),
		mul = window.devicePixelRatio || 1;

	r.w = b.width;
	r.h = b.height;
	can.width = r.w * mul;
	can.height = r.h * mul;

	r.can = can;
	r.ctx = can.getContext('2d');
	r.ctx.scale(mul, mul);
	return r;
}


function glossy_grad(can, h, s, l) {
	var g = can.ctx.createLinearGradient(0, 0, 0, can.h),
		p = [0, 0.49, 0.50, 1];

	for (var a = 0; a < p.length; a++)
		g.addColorStop(p[a], 'hsl(' + h + ',' + s[a] + '%,' + l[a] + '%)');

	return g;
}


// buffer/position bar
var pbar = (function () {
	var r = {},
		bau = null,
		html_txt = 'a',
		lastmove = 0,
		mousepos = 0,
		t_redraw = 0,
		gradh = -1,
		grad;

	r.onresize = function () {
		if (!widget.is_open && r.buf)
			return;

		r.buf = canvas_cfg(ebi('barbuf'));
		r.pos = canvas_cfg(ebi('barpos'));
		r.buf.ctx.font = '.5em sans-serif';
		r.pos.ctx.font = '.9em sans-serif';
		r.pos.ctx.strokeStyle = 'rgba(24,56,0,0.5)';
		r.drawbuf();
		r.drawpos();
		if (!r.pos.can.onmouseleave)
			mleave();
	};

	r.loadwaves = function (url) {
		r.wurl = url;
		var img = new Image();
		img.onload = function () {
			if (r.wurl != url)
				return;

			r.wimg = img;
			r.onresize();
		};
		img.src = url;
	};

	r.unwave = function () {
		r.wurl = r.wimg = null;
	}

	function mmove(e) {
		var adur;
		if (e.buttons || !mp || !mp.au || !isNum(adur = mp.au.duration))
			return;

		var rect = r.pos.can.getBoundingClientRect(),
			x = e.clientX - rect.left,
			mul = x * 1.0 / rect.width;

		mousepos = adur * mul;
		lastmove = Date.now();
		r.drawpos();
	}
	function menter() {
		r.pos.can.onmousemove = mmove;
		r.pos.can.onmouseleave = mleave;
	}
	function mleave() {
		r.pos.can.onmousemove = null;
		r.pos.can.onmouseleave = null;
		r.pos.can.onmouseenter = menter;
		if (lastmove) {
			lastmove = 0;
			r.drawpos();
		}
	}

	r.drawbuf = function () {
		var bc = r.buf,
			pc = r.pos,
			bctx = bc.ctx,
			apos, adur;

		if (!widget.is_open)
			return;

		bctx.clearRect(0, 0, bc.w, bc.h);

		if (!mp || !mp.au || !isNum(adur = mp.au.duration) || !isNum(apos = mp.au.currentTime) || apos < 0 || adur < apos)
			return;  // not-init || unsupp-codec

		bau = mp.au;

		var sm = bc.w * 1.0 / mp.au.duration,
			gk = bc.h + '/' + themen,
			dz = themen == 'dz',
			dy = themen == 'dy';

		if (gradh != gk) {
			gradh = gk;
			grad = glossy_grad(bc, dz ? 120 : 85,
				dy ? [0, 0, 0, 0] : [35, 40, 37, 35],
				dy ? [20, 24, 22, 20] : light ? [45, 56, 50, 45] : [42, 51, 47, 42]);
		}
		bctx.fillStyle = grad;
		for (var a = 0; a < mp.au.buffered.length; a++) {
			var x1 = sm * mp.au.buffered.start(a),
				x2 = sm * mp.au.buffered.end(a);

			bctx.fillRect(x1, 0, x2 - x1, bc.h);
		}
		if (r.wimg) {
			bctx.globalAlpha = 0.6;
			bctx.filter = light ? '' : 'invert(1)';
			bctx.drawImage(r.wimg, 0, 0, bc.w, bc.h);
			bctx.filter = 'invert(0)';
			bctx.globalAlpha = 1;
		}

		var step = sm > 1 ? 1 : sm > 0.4 ? 3 : sm > 0.05 ? 30 : 720;
		bctx.fillStyle = light && !dy ? 'rgba(0,64,0,0.15)' : 'rgba(204,255,128,0.15)';
		for (var p = step, mins = adur / 10; p <= mins; p += step)
			bctx.fillRect(Math.floor(sm * p * 10), 0, 2, pc.h);

		step = sm > 0.15 ? 1 : sm > 0.05 ? 10 : 360;
		bctx.fillStyle = light && !dy ? 'rgba(0,64,0,0.5)' : 'rgba(192,255,96,0.5)';
		for (var p = step, mins = adur / 60; p <= mins; p += step)
			bctx.fillRect(Math.floor(sm * p * 60), 0, 2, pc.h);

		step = sm > 0.33 ? 1 : sm > 0.15 ? 5 : sm > 0.05 ? 10 : sm > 0.01 ? 60 : 720;
		bctx.fillStyle = dz ? '#0f0' : dy ? '#999' : light ? 'rgba(0,64,0,0.9)' : 'rgba(192,255,96,1)';
		for (var p = step, mins = adur / 60; p <= mins; p += step) {
			bctx.fillText(p, Math.floor(sm * p * 60 + 3), pc.h / 3);
		}

		step = sm > 0.2 ? 10 : sm > 0.1 ? 30 : sm > 0.01 ? 60 : sm > 0.005 ? 720 : 1440;
		bctx.fillStyle = light ? 'rgba(0,0,0,1)' : 'rgba(255,255,255,1)';
		for (var p = step, mins = adur / 60; p <= mins; p += step)
			bctx.fillRect(Math.floor(sm * p * 60), 0, 2, pc.h);
	};

	r.drawpos = function () {
		var bc = r.buf,
			pc = r.pos,
			pctx = pc.ctx,
			w = 8,
			apos, adur;

		if (t_redraw) {
			clearTimeout(t_redraw);
			t_redraw = 0;
		}
		pctx.clearRect(0, 0, pc.w, pc.h);

		if (!mp || !mp.au)
			return;  // not-init

		if (!isNum(adur = mp.au.duration) || !isNum(apos = mp.au.currentTime) || apos < 0 || adur < apos) {
			if (Date.now() - mp.au.pt0 < 500)
				return;

			pctx.fillStyle = light ? 'rgba(0,0,0,0.5)' : 'rgba(255,255,255,0.5)';
			var m = /[?&]th=(opus|owa|caf|mp3)/.exec('' + mp.au.rsrc),
				txt = mp.au.ded ? L.mm_playerr.replace(':', ' ;_;') :
					m ? L.mm_bconv.format(m[1]) : L.mm_bload;

			pctx.fillText(txt, 16, pc.h / 1.5);
			return;  // not-init || unsupp-codec
		}

		if (bau != mp.au)
			r.drawbuf();

		if (Date.now() - lastmove < 400) {
			apos = mousepos;
			w = 0;
		}

		var sm = bc.w * 1.0 / adur,
			t1 = s2ms(adur),
			t2 = s2ms(apos),
			x = sm * apos;

		if (w && html_txt != t2) {
			ebi('np_pos').textContent = html_txt = t2;
			if (mpl.os_ctl)
				navigator.mediaSession.setPositionState({
					'duration': adur,
					'position': apos,
					'playbackRate': 1
				});
		}

		if (!widget.is_open)
			return;

		pctx.fillStyle = '#573'; pctx.fillRect((x - w / 2) - 1, 0, w + 2, pc.h);
		pctx.fillStyle = '#dfc'; pctx.fillRect((x - w / 2), 0, w, pc.h);

		pctx.lineWidth = 2.5;
		pctx.fillStyle = '#fff';

		var m1 = pctx.measureText(t1),
			m1b = pctx.measureText(t1 + ":88"),
			m2 = pctx.measureText(t2),
			yt = pc.h * 0.94,
			xt1 = pc.w - (m1.width + 12),
			xt2 = x < m1.width * 1.4 ? (x + 12) : (Math.min(pc.w - m1b.width, x - 12) - m2.width);

		pctx.strokeText(t1, xt1 + 1, yt + 1);
		pctx.strokeText(t2, xt2 + 1, yt + 1);
		pctx.strokeText(t1, xt1, yt);
		pctx.strokeText(t2, xt2, yt);
		pctx.fillText(t1, xt1, yt);
		pctx.fillText(t2, xt2, yt);

		if (sm > 10)
			t_redraw = setTimeout(r.drawpos, sm > 50 ? 20 : 50);
	};

	onresize100.add(r.onresize, true);
	return r;
})();


// volume bar
var vbar = (function () {
	var r = {},
		gradh = -1,
		lastv = -1,
		untext = -1,
		can, ctx, w, h, grad1, grad2;

	r.onresize = function () {
		if (!widget.is_open && r.can)
			return;

		r.can = canvas_cfg(ebi('pvol'));
		can = r.can.can;
		ctx = r.can.ctx;
		ctx.font = '.7em sans-serif';
		ctx.fontVariantCaps = 'small-caps';
		w = r.can.w;
		h = r.can.h;
		r.draw();
	}

	r.draw = function () {
		if (!mp)
			return;

		var gh = h + '' + light,
			dz = themen == 'dz',
			dy = themen == 'dy';

		if (gradh != gh) {
			gradh = gh;
			grad1 = glossy_grad(r.can, dz ? 120 : 50,
				dy ? [0, 0, 0, 0] : light ? [50, 55, 52, 48] : [45, 52, 47, 43],
				dy ? [20, 24, 22, 20] : light ? [54, 60, 52, 47] : [42, 51, 47, 42]);
			grad2 = glossy_grad(r.can, dz ? 120 : 205,
				dz ? [100, 100, 100, 100] : dy ? [0, 0, 0, 0] : [10, 15, 13, 10],
				dz ? [10, 14, 12, 10] : dy ? [90, 90, 90, 90] : [16, 20, 18, 16]);
		}
		ctx.fillStyle = grad2; ctx.fillRect(0, 0, w, h);
		ctx.fillStyle = grad1; ctx.fillRect(0, 0, w * mp.vol, h);

		var vt = 'volume ' + Math.floor(mp.vol * 100),
			tw = ctx.measureText(vt).width,
			x = w * mp.vol - tw - 8,
			li = dy;

		if (mp.vol < 0.5) {
			x += tw + 16;
			li = !li;
		}

		ctx.fillStyle = li ? '#fff' : '#210';
		ctx.fillText(vt, x, h / 3 * 2);

		clearTimeout(untext);
		untext = setTimeout(r.draw, 1000);
	};
	onresize100.add(r.onresize, true);

	var rect;
	function mousedown(e) {
		rect = can.getBoundingClientRect();
		mousemove(e);
	}
	function mousemove(e) {
		if (e.changedTouches && e.changedTouches.length > 0) {
			e = e.changedTouches[0];
		}
		else if (e.buttons === 0) {
			can.onmousemove = null;
			return;
		}

		var x = e.clientX - rect.left,
			mul = x * 1.0 / rect.width;

		if (mul > 0.98)
			mul = 1;

		lastv = Date.now();
		mp.setvol(mul);
		r.draw();

		setTimeout(function () {
			if (IPHONE && mp.au && mul < 0.9 && mp.au.volume == 1)
				toast.inf(6, 'volume doesnt work because <a href="https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/Using_HTML5_Audio_Video/Device-SpecificConsiderations/Device-SpecificConsiderations.html#//apple_ref/doc/uid/TP40009523-CH5-SW11" target="_blank">apple says no</a>');
		}, 1);
	}
	can.onmousedown = function (e) {
		if (e.button !== 0)
			return;

		can.onmousemove = mousemove;
		mousedown(e);
	};
	can.onmouseup = function (e) {
		if (e.button === 0)
			can.onmousemove = null;
	};
	if (TOUCH) {
		can.ontouchstart = mousedown;
		can.ontouchmove = mousemove;
	}
	return r;
})();


function seek_au_mul(mul) {
	if (mp.au)
		seek_au_sec(mp.au.duration * mul);
}

function seek_au_rel(sec) {
	if (mp.au)
		seek_au_sec(mp.au.currentTime + sec);
}

function seek_au_sec(seek) {
	if (!mp.au)
		return;

	console.log('seek: ' + seek);
	if (!isNum(seek))
		return;

	mp.nopause();
	mp.au.currentTime = seek;

	if (mp.au.paused)
		mp.fade_in();

	mpui.progress_updater();
}


function song_skip(n, dirskip) {
	var tid = mp.au && mp.au.evp == get_evpath() ? mp.au.tid : null,
		ofs = tid ? mp.order.indexOf(tid) : -1;

	if (dirskip && ofs + 1 && ofs > mp.order.length - 2) {
		toast.inf(10, L.mm_nof);
		console.log("mm_nof1");
		mpl.traversals = 0;
		return;
	}

	if (tid && !dirskip)
		play(ofs + n);
	else
		play(mp.order[n == -1 ? mp.order.length - 1 : 0]);
}
function next_song(e) {
	ev(e);
	if (QS('.dumb_loader_thing')) {
		treectl.ls_cb = next_song;
		return;
	}
	if (mp.order.length) {
		var dirskip = mpl.traversals;
		mpl.traversals = 0;
		return song_skip(1, dirskip);
	}
	if (mpl.traversals++ < 5) {
		treectl.ls_cb = next_song;
		return tree_neigh(1);
	}
	toast.inf(10, L.mm_nof);
	console.log("mm_nof2");
	mpl.traversals = 0;
}
function last_song(e) {
	ev(e);
	if (mp.order.length) {
		mpl.traversals = 0;
		return song_skip(-1, true);
	}
	if (mpl.traversals++ < 5) {
		treectl.ls_cb = last_song;
		return tree_neigh(-1);
	}
	toast.inf(10, L.mm_nof);
	console.log("mm_nof2");
	mpl.traversals = 0;
}
function prev_song(e) {
	ev(e);

	if (mp.au && !mp.au.paused && mp.au.currentTime > 3)
		return seek_au_sec(0);

	if (QS('.dumb_loader_thing')) {
		treectl.ls_cb = function () { song_skip(-1); };
		return;
	}
	return song_skip(-1);
}
function dl_song() {
	if (!mp || !mp.au) {
		var o = QSA('#files a[id]');
		for (var a = 0; a < o.length; a++)
			o[a].setAttribute('download', '');

		return toast.inf(10, L.f_dls);
	}

	var url = addq(mp.au.osrc, 'cache=987&_=' + ACB);
	dl_file(url);
}
function sel_song() {
	var o = QS('#files tr.play');
	if (!o)
		return;
	clmod(o, 'sel', 't');
	msel.origin_tr(o);
	msel.selui();
}


function playpause(e) {
	// must be event-chain
	ev(e);
	if (mp.au) {
		if (mp.au.paused)
			mp.fade_in();
		else
			mp.fade_out();

		mpui.progress_updater();
	}
	else
		play(0, true);

	mpl.pp();
};


function mplay(e) {
	if (mp.au && !mp.au.paused)
		return;

	playpause(e);
}


function mpause(e) {
	if (mp.cd_pause > Date.now() - 100)
		return;

	if (mp.au && mp.au.paused)
		return;

	playpause(e);
}


// hook up the widget buttons
(function () {
	ebi('bplay').onclick = playpause;
	ebi('bprev').onclick = prev_song;
	ebi('bnext').onclick = next_song;

	var bar = ebi('barpos');

	bar.onclick = function (e) {
		if (!mp.au) {
			play(0, true);
			return mp.fade_in();
		}

		var rect = pbar.buf.can.getBoundingClientRect(),
			x = e.clientX - rect.left;

		seek_au_mul(x * 1.0 / rect.width);
	};

	if (!TOUCH) {
		bar.onwheel = function (e) {
			var dist = Math.sign(e.deltaY) * 10;
			if (Math.abs(e.deltaY) < 30 && !e.deltaMode)
				dist = e.deltaY;

			if (!dist || !mp.au)
				return true;

			seek_au_rel(dist);
			ev(e);
		};
		ebi('pvol').onwheel = function (e) {
			var dist = Math.sign(e.deltaY) * 10;
			if (Math.abs(e.deltaY) < 30 && !e.deltaMode)
				dist = e.deltaY;

			if (!dist || !mp.au)
				return true;

			dist *= -1;
			mp.setvol(mp.vol + dist / 500);
			vbar.draw();
			ev(e);
		};
	}
})();


// periodic tasks
var mpui = (function () {
	var r = {},
		nth = 0,
		preloaded = null,
		fpreloaded = null;

	r.progress_updater = function () {
		//console.trace();
		timer.add(updater_impl, true);
	};

	function repreload() {
		preloaded = fpreloaded = null;
	}

	function updater_impl() {
		if (!mp.au) {
			widget.paused(true);
			timer.rm(updater_impl);
			return;
		}

		var paint = !MOBILE || document.hasFocus();

		var pos = mp.au.currentTime;
		if (!isNum(pos))
			pos = 0;

		// indicate playback state in ui
		widget.paused(mp.au.paused);

		if (paint && ++nth > 69) {
			// android-chrome breaks aspect ratio with unannounced viewport changes
			nth = 0;
			if (MOBILE) {
				nth = 1;
				pbar.onresize();
				vbar.onresize();
			}
		}
		else if (paint) {
			// draw current position in song
			if (!mp.au.paused)
				pbar.drawpos();

			// occasionally draw buffered regions
			if (nth % 5 == 0)
				pbar.drawbuf();
		}

		// preload next song
		if (!mpl.one && mpl.preload && preloaded != mp.au.rsrc) {
			var len = mp.au.duration,
				rem = pos > 1 ? len - pos : 999,
				full = null;

			if (rem < 7 || (!mpl.fullpre && (rem < 40 || (rem < 90 && pos > 10)))) {
				preloaded = fpreloaded = mp.au.rsrc;
				full = false;
			}
			else if (rem < 60 && mpl.fullpre && fpreloaded != mp.au.rsrc) {
				fpreloaded = mp.au.rsrc;
				full = true;
			}

			if (full !== null)
				try {
					var oi = mp.order.indexOf(mp.au.tid) + 1,
						evp = get_evpath();

					if (oi >= mp.order.length && (
							mpl.one ||
							mpl.pb_mode != 'next' ||
							mp.au.evp != evp ||
							ebi('unsearch'))
						)
						oi = 0;

					if (oi >= mp.order.length) {
						if (!mpl.prescan)
							throw "prescan disabled";

						if (mpl.prescan_evp == evp)
							throw "evp match";

						if (mpl.traversals++ > 4) {
							mpl.prescan_evp = null;
							toast.inf(10, L.mm_nof);
							throw L.mm_nof;
						}

						mpl.prescan_evp = evp;
						toast.inf(10, L.mm_prescan);
						treectl.ls_cb = repreload;
						tree_neigh(1);
					}
					else
						mp.preload(mp.tracks[mp.order[oi]], full);
				}
				catch (ex) {
					console.log("preload failed", ex);
				}
		}

		if (mp.au.paused)
			timer.rm(updater_impl);
	}
	return r;
})();


// event from play button next to a file in the list
function ev_play(e) {
	ev(e);

	var fade = !mp.au || mp.au.paused;
	play(this.getAttribute('id').slice(1), true);
	if (fade)
		mp.fade_in();

	return false;
}


var actx = null;

function start_actx() {
	// bonus: speedhack for unfocused file hashing (removes 1sec delay on subtle.digest resolves)
	if (!actx) {
		if (!ACtx)
			return;

		actx = new ACtx();
		console.log('actx created');
	}
	try {
		if (actx.state == 'suspended') {
			actx.resume();
			setTimeout(function () {
				console.log('actx is ' + actx.state);
			}, 500);
		}
	}
	catch (ex) {
		console.log('actx start failed; ' + ex);
	}
}

var afilt = (function () {
	var r = {
		"eqen": false,
		"drcen": false,
		"bands": [31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000],
		"gains": [4, 3, 2, 1, 0, 0, 1, 2, 3, 4],
		"drcv": [-24, 30, 12, 0.01, 0.25],
		"drch": ['tresh', 'knee', 'ratio', 'atk', 'rls'],
		"drck": ['threshold', 'knee', 'ratio', 'attack', 'release'],
		"drcn": null,
		"filters": [],
		"filterskip": [],
		"plugs": [],
		"amp": 0,
		"chw": 1,
		"last_au": null,
		"acst": {}
	};

	function setvis(vis) {
		ebi('audio_eq').parentNode.style.display = ebi('audio_drc').parentNode.style.display = (vis ? '' : 'none');
	}

	setvis(ACtx);

	r.init = function () {
		start_actx();
		if (r.cfg)
			return;

		setvis(actx);

		// some browsers have insane high-frequency boost
		// (or rather the actual problem is Q but close enough)
		r.cali = (function () {
			try {
				var fi = actx.createBiquadFilter(),
					freqs = new Float32Array(1),
					mag = new Float32Array(1),
					phase = new Float32Array(1);

				freqs[0] = 14000;
				fi.type = 'peaking';
				fi.frequency.value = 18000;
				fi.Q.value = 0.8;
				fi.gain.value = 1;
				fi.getFrequencyResponse(freqs, mag, phase);

				return mag[0];  // 1.0407 good, 1.0563 bad
			}
			catch (ex) {
				return 0;
			}
		})();
		console.log('eq cali: ' + r.cali);

		var e1 = r.cali < 1.05;

		r.cfg = [ // hz, q, g
			[31.25 * 0.88, 0, 1.4],  // shelf
			[31.25 * 1.04, 0.7, 0.96],  // peak
			[62.5, 0.7, 1],
			[125, 0.8, 1],
			[250, 0.9, 1.03],
			[500, 0.9, 1.1],
			[1000, 0.9, 1.1],
			[2000, 0.9, 1.105],
			[4000, 0.88, 1.05],
			[8000 * 1.006, 0.73, e1 ? 1.24 : 1.2],
			[16000 * 0.89, 0.7, e1 ? 1.26 : 1.2],  // peak
			[16000 * 1.13, 0.82, e1 ? 1.09 : 0.75],  // peak
			[16000 * 1.205, 0, e1 ? 1.9 : 1.85]  // shelf
		];
	};

	try {
		r.amp = fcfg_get('au_eq_amp', r.amp);
		r.chw = fcfg_get('au_eq_chw', r.chw);
		var gains = jread('au_eq_gain', r.gains);
		if (r.gains.length == gains.length)
			r.gains = gains;

		r.drcv = jread('au_drcv', r.drcv);
	}
	catch (ex) { }

	r.draw = function () {
		jwrite('au_eq_gain', r.gains);
		swrite('au_eq_amp', r.amp);
		swrite('au_eq_chw', r.chw);

		var txt = QSA('input.eq_gain');
		for (var a = 0; a < r.bands.length; a++)
			txt[a].value = r.gains[a];

		QS('input.eq_gain[band="amp"]').value = r.amp;
		QS('input.eq_gain[band="chw"]').value = r.chw;
	};

	r.stop = function () {
		if (r.filters.length)
			for (var a = 0; a < r.filters.length; a++)
				r.filters[a].disconnect();

		r.filters = [];
		r.filterskip = [];

		for (var a = 0; a < r.plugs.length; a++)
			r.plugs[a].unload();

		if (!mp)
			return;

		if (mp.acs)
			mp.acs.disconnect();

		mp.acs = mpo.acs = null;
	};

	r.apply = function (v, au) {
		r.init();
		r.draw();

		if (!actx) {
			bcfg_set('au_eq', r.eqen = false);
			bcfg_set('au_drc', r.drcen = false);
		}
		else if (v === true && r.drcen && !r.eqen)
			bcfg_set('au_eq', r.eqen = true);
		else if (v === false && !r.eqen)
			bcfg_set('au_drc', r.drcen = false);

		r.drcn = null;

		var plug = false;
		for (var a = 0; a < r.plugs.length; a++)
			if (r.plugs[a].en)
				plug = true;

		au = au || (mp && mp.au);
		if (!actx || !au || (!r.eqen && !plug && !mp.acs))
			return;

		r.stop();
		au.id = au.id || Date.now();
		mp.acs = r.acst[au.id] = r.acst[au.id] || actx.createMediaElementSource(au);

		if (r.eqen)
			add_eq();

		for (var a = 0; a < r.plugs.length; a++)
			if (r.plugs[a].en)
				r.plugs[a].load();

		for (var a = 0; a < r.filters.length; a++)
			if (!has(r.filterskip, a))
				r.filters[a].connect(a ? r.filters[a - 1] : actx.destination);

		mp.acs.connect(r.filters.length ?
			r.filters[r.filters.length - 1] : actx.destination);
	}

	function add_eq() {
		var min, max;
		min = max = r.gains[0];
		for (var a = 1; a < r.gains.length; a++) {
			min = Math.min(min, r.gains[a]);
			max = Math.max(max, r.gains[a]);
		}

		var gains = [];
		for (var a = 0; a < r.gains.length; a++)
			gains.push(r.gains[a] - max);

		var t = gains[gains.length - 1];
		gains.push(t);
		gains.push(t);
		gains.unshift(gains[0]);

		for (var a = 0; a < r.cfg.length && min != max; a++) {
			var fi = actx.createBiquadFilter(), c = r.cfg[a];
			fi.frequency.value = c[0];
			fi.gain.value = c[2] * gains[a];
			fi.Q.value = c[1];
			fi.type = a == 0 ? 'lowshelf' : a == r.cfg.length - 1 ? 'highshelf' : 'peaking';
			r.filters.push(fi);
		}

		// pregain, keep first in chain
		fi = actx.createGain();
		fi.gain.value = r.amp + 0.94;  // +.137 dB measured; now -.25 dB and almost bitperfect
		r.filters.push(fi);

		// wait nevermind, drc goes first
		timer.rm(showdrc);
		if (r.drcen) {
			fi = r.drcn = actx.createDynamicsCompressor();
			for (var a = 0; a < r.drcv.length; a++)
				fi[r.drck[a]].value = r.drcv[a];

			if (r.drcv[3] < 0.02) {
				// avoid static at decode start
				fi.attack.value = 0.02;
				setTimeout(function () {
					try {
						fi.attack.value = r.drcv[3];
					}
					catch (ex) { }
				}, 200);
			}

			r.filters.push(fi);
			timer.add(showdrc);
		}

		if (Math.round(r.chw * 25) != 25) {
			var split = actx.createChannelSplitter(2),
				merge = actx.createChannelMerger(2),
				lg1 = actx.createGain(),
				lg2 = actx.createGain(),
				rg1 = actx.createGain(),
				rg2 = actx.createGain(),
				vg1 = 1 - (1 - r.chw) / 2,
				vg2 = 1 - vg1;

			console.log('chw', vg1, vg2);

			merge.connect(r.filters[r.filters.length - 1]);
			lg1.gain.value = rg2.gain.value = vg1;
			lg2.gain.value = rg1.gain.value = vg2;
			lg1.connect(merge, 0, 0);
			rg1.connect(merge, 0, 0);
			lg2.connect(merge, 0, 1);
			rg2.connect(merge, 0, 1);

			split.connect(lg1, 0);
			split.connect(lg2, 0);
			split.connect(rg1, 1);
			split.connect(rg2, 1);
			r.filterskip.push(r.filters.length);
			r.filters.push(split);
			mp.acs.channelCountMode = 'explicit';
		}
	}

	function eq_step(e) {
		ev(e);
		var sb = this.getAttribute('band'),
			band = parseInt(sb),
			step = parseFloat(this.getAttribute('step'));

		if (sb == 'amp')
			r.amp = Math.round((r.amp + step * 0.2) * 100) / 100;
		else if (sb == 'chw')
			r.chw = Math.round((r.chw + step * 0.2) * 100) / 100;
		else
			r.gains[band] += step;

		r.apply();
	}

	function adj_band(that, step) {
		var err = false;
		try {
			var sb = that.getAttribute('band'),
				band = parseInt(sb),
				vs = that.value,
				v = parseFloat(vs);

			if (!isNum(v) || v + '' != vs)
				throw new Error('inval band');

			if (sb == 'amp')
				r.amp = Math.round((v + step * 0.2) * 100) / 100;
			else if (sb == 'chw')
				r.chw = Math.round((v + step * 0.2) * 100) / 100;
			else
				r.gains[band] = v + step;

			r.apply();
		}
		catch (ex) {
			err = true;
		}
		clmod(that, 'err', err);
	}

	function adj_drc() {
		var err = false;
		try {
			var n = this.getAttribute('k'),
				ov = r.drcv[n],
				vs = this.value,
				v = parseFloat(vs);

			if (!isNum(v) || v + '' != vs)
				throw new Error('inval v');

			if (v == ov)
				return;

			r.drcv[n] = v;
			jwrite('au_drcv', r.drcv);
			if (r.drcn)
				r.drcn[r.drck[n]].value = v;
		}
		catch (ex) {
			err = true;
		}
		clmod(this, 'err', err);
	}

	function eq_mod(e) {
		ev(e);
		adj_band(this, 0);
	}

	function eq_keydown(e) {
		var step = e.key == 'ArrowUp' ? 0.25 : e.key == 'ArrowDown' ? -0.25 : 0;
		if (step != 0)
			adj_band(this, step);
	}

	function showdrc() {
		if (!r.drcn)
			return timer.rm(showdrc);

		ebi('h_drc').textContent = f2f(r.drcn.reduction, 1);
	}

	var html = ['<table><tr><td rowspan="4">',
		'<a id="au_eq" class="tgl btn" href="#" tt="' + L.mt_eq + '">' + L.enable + '</a></td>'],
		h2 = [], h3 = [], h4 = [];

	var vs = [];
	for (var a = 0; a < r.bands.length; a++) {
		var hz = r.bands[a];
		if (hz >= 1000)
			hz = (hz / 1000) + 'k';

		hz = (hz + '').split('.')[0];
		vs.push([a, hz, r.gains[a]]);
	}
	vs.push(["amp", "boost", r.amp]);
	vs.push(["chw", "width", r.chw]);

	for (var a = 0; a < vs.length; a++) {
		var b = vs[a][0];
		html.push('<td><a href="#" class="eq_step" step="0.5" band="' + b + '">+</a></td>');
		h2.push('<td>' + vs[a][1] + '</td>');
		h4.push('<td><a href="#" class="eq_step" step="-0.5" band="' + b + '">&ndash;</a></td>');
		h3.push('<td><input type="text" class="eq_gain" ' + NOAC + ' band="' + b + '" value="' + vs[a][2] + '" /></td>');
	}
	html = html.join('\n') + '</tr><tr>';
	html += h2.join('\n') + '</tr><tr>';
	html += h3.join('\n') + '</tr><tr>';
	html += h4.join('\n') + '</tr><table>';
	ebi('audio_eq').innerHTML = html;

	h2 = [];
	html = ['<table><tr><td rowspan="2">',
		'<a id="au_drc" class="tgl btn" href="#" tt="' + L.mt_drc + '">' + L.enable + '</a></td>'];

	for (var a = 0; a < r.drch.length; a++) {
		html.push('<td>' + r.drch[a] + '</td>');
		h2.push('<td><input type="text" class="drc_v" ' + NOAC + ' k="' + a + '" value="' + r.drcv[a] + '" /></td>');
	}
	html = html.join('\n') + '</tr><tr>';
	html += h2.join('\n') + '</tr><table>';
	ebi('audio_drc').innerHTML = html;

	var stp = QSA('a.eq_step');
	for (var a = 0, aa = stp.length; a < aa; a++)
		stp[a].onclick = eq_step;

	var txt = QSA('input.eq_gain');
	for (var a = 0; a < txt.length; a++) {
		txt[a].oninput = eq_mod;
		txt[a].onkeydown = eq_keydown;
	}
	txt = QSA('input.drc_v');
	for (var a = 0; a < txt.length; a++)
		txt[a].oninput = txt[a].onkeydown = adj_drc;

	bcfg_bind(r, 'eqen', 'au_eq', false, r.apply);
	bcfg_bind(r, 'drcen', 'au_drc', false, r.apply);

	r.draw();
	return r;
})();


// plays the tid'th audio file on the page
function play(tid, is_ev, seek) {
	clearTimeout(mpl.t_eplay);
	if (mp.order.length == 0)
		return console.log('no audio found wait what');

	if (crashed)
		return;

	mpl.preload_url = null;
	mp.nopause();
	mp.stopfade(true);

	var tn = tid;
	if ((tn + '').indexOf('f-') === 0) {
		tn = mp.order.indexOf(tn);
		if (tn < 0)
			return toast.warn(10, L.mm_hnf);
	}

	if (tn >= mp.order.length) {
		if (mpl.pb_mode == 'stop')
			return;

		if (mpl.pb_mode == 'loop' || ebi('unsearch')) {
			tn = 0;
		}
		else if (mpl.pb_mode == 'next') {
			treectl.ls_cb = next_song;
			return tree_neigh(1);
		}
	}

	if (tn < 0) {
		if (mpl.pb_mode == 'loop') {
			tn = mp.order.length - 1;
		}
		else if (mpl.pb_mode == 'next') {
			treectl.ls_cb = last_song;
			return tree_neigh(-1);
		}
	}

	tid = mp.order[tn];

	if (mp.au) {
		mp.au.pause();
		var el = ebi('a' + mp.au.tid);
		if (el)
			clmod(el, 'act');
	}
	else {
		mp.au = new Audio();
		mp.au2 = new Audio();
		mp.set_ev();
		widget.open();
	}
	mp.init_fau();

	var url = addq(mpl.acode(mp.tracks[tid]), 'cache=987&_=' + ACB);

	if (mp.au.rsrc == url)
		mp.au.currentTime = 0;
	else if (mp.au2.rsrc == url) {
		var t = mp.au;
		mp.au = mp.au2;
		mp.au2 = t;
		t.onerror = t.onprogress = t.onended = t.loop = null;
		t.ld = 0; //owa
		mp.set_ev();
		t = mp.au.currentTime;
		if (isNum(t) && t > 0.1)
			mp.au.currentTime = 0;
	}
	else {
		console.log('get ' + url.split('/').pop());
		mp.au.src = mp.au.rsrc = url;
	}

	mp.au.osrc = mp.tracks[tid];
	afilt.apply();

	setTimeout(function () {
		mpl.unbuffer(url);
	}, 500);

	mp.au.ded = 0;
	mp.au.tid = tid;
	mp.au.pt0 = Date.now();
	mp.au.evp = get_evpath();
	mp.au.volume = mp.expvol(mp.vol);
	var trs = QSA('#files tr.play');
	for (var a = 0, aa = trs.length; a < aa; a++)
		clmod(trs[a], 'play');

	var oid = 'a' + tid;
	clmod(ebi(oid), 'act', 1);
	clmod(ebi(oid).closest('tr'), 'play', 1);
	clmod(ebi('wtoggle'), 'np', mpl.clip);
	clmod(ebi('wtoggle'), 'm3u', mpl.m3uen);
	if (thegrid)
		thegrid.loadsel();

	if (mpl.follow)
		scroll2playing();

	try {
		mp.nopause();
		mp.au.loop = mpl.loop && !mpl.one;
		if (mpl.aplay || is_ev !== -1)
			mp.au.play();

		if (mp.au.paused)
			autoplay_blocked(seek);
		else if (seek) {
			seek_au_sec(seek);
		}

		if (!seek && !ebi('unsearch')) {
			var o = ebi(oid);
			o.setAttribute('id', 'thx_js');
			if (mpl.aplay)
				sethash(oid + getsort());
			o.setAttribute('id', oid);
		}

		pbar.unwave();
		if (mpl.waves)
			pbar.loadwaves(url.replace(/\bth=(opus|mp3)&/, '') + '&th=p');

		mpui.progress_updater();
		pbar.onresize();
		vbar.onresize();
		mpl.announce();
		return true;
	}
	catch (ex) {
		toast.err(0, esc(L.mm_playerr + basenames(ex)));
	}
	clmod(ebi(oid), 'act');
	mpl.t_eplay = setTimeout(next_song, 5000);
}


function scroll2playing() {
	try {
		QS((!thegrid || !thegrid.en) ?
			'tr.play' : '#ggrid a.play').scrollIntoView();
	}
	catch (ex) { }
}


function evau_end(e) {
	if (mpl.one)
		return;
	if (!mpl.loop)
		return next_song(e);
	ev(e);
	mp.au.currentTime = 0;
	mp.au.play();
}


// event from the audio object if something breaks
function evau_error(e) {
	var err = '',
		eplaya = (e && e.target) || (window.event && window.event.srcElement);

	eplaya.ded = 1;

	switch (eplaya.error.code) {
		case eplaya.error.MEDIA_ERR_ABORTED:
			err = L.mm_eabrt;
			break;
		case eplaya.error.MEDIA_ERR_NETWORK:
			if (IPHONE && eplaya.ld === 1 && mpl.ac2 == 'owa' && !eplaya.paused && !eplaya.currentTime) {
				eplaya.ded = 0;
				if (!mpl.owaw) {
					mpl.owaw = 1;
					console.log('ignored iOS bug; spurious error sent in parallel with preloaded songs starting to play just fine');
				}
				return;
			}
			err = L.mm_enet;
			break;
		case eplaya.error.MEDIA_ERR_DECODE:
			err = L.mm_edec;
			break;
		case eplaya.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
			err = L.mm_esupp;
			if (/\.(aac|m4a)(\?|$)/i.exec(eplaya.rsrc) && !mpl.ac_aac) {
				try {
					ebi('ac_aac').click();
					QS('a.play.act').click();
					toast.warn(10, L.mm_opusen);
					return;
				}
				catch (ex) { }
			}
			break;
		default:
			err = L.mm_eunk;
			break;
	}
	var em = '' + eplaya.error.message,
		mfile = '\n\nFile: «' + uricom_dec(eplaya.src.split('/').pop()) + '»',
		e500 = L.mm_e500,
		e404 = L.mm_e404,
		e403 = L.mm_e403;

	if (em)
		err += '\n\n' + em;

	if (em.startsWith('403: '))
		err = e403;

	if (em.startsWith('404: '))
		err = e404;

	if (em.startsWith('500: '))
		err = e500;

	toast.warn(15, esc(basenames(err + mfile)));
	console.log(basenames(err + mfile));

	if (em.startsWith('MEDIA_ELEMENT_ERROR:')) {
		// chromish for 40x
		var xhr = new XHR();
		xhr.open('HEAD', eplaya.src, true);
		xhr.onload = xhr.onerror = function () {
			if (this.status < 400)
				return;

			err = this.status == 403 ? e403 :
				this.status == 404 ? e404 :
				this.status == 500 ? e500 :
				L.mm_e5xx + this.status;

			toast.warn(15, esc(basenames(err + mfile)));
		};
		xhr.send();
		return;
	}

	mpl.t_eplay = setTimeout(next_song, 15000);
}


// show ui to manually start playback of a linked song
function autoplay_blocked(seek) {
	var tid = mp.au.tid,
		fn = mp.tracks[tid].split(/\//).pop();

	fn = uricom_dec(fn.replace(/\+/g, ' ').split('?')[0]);

	modal.confirm('<h6>' + L.mm_hashplay + '</h6>\n«' + esc(fn) + '»', function () {
		// chrome 91 may permanently taint on a failed play()
		// depending on win10 settings or something? idk
		mp.au = mpo.au = null;

		play(tid, true, seek);
		mp.fade_in();
	}, function () {
		sethash('');
		clmod(QS('#files tr.play'), 'play');
		return reload_mp();
	});
}


function scan_hash(v) {
	if (!v)
		return null;

	var m = /^#([ag])(f-[0-9a-f]{8,16})(&.+)?/.exec(v + '');
	if (!m)
		return null;

	var mtype = m[1],
		id = m[2],
		ts = null;

	if (m.length > 3) {
		var tm = /^&[Tt=0]*([0-9]+[Mm:])?0*([0-9\.]+)[Ss]?$/.exec(m[3]);
		if (tm) {
			ts = parseInt(tm[1] || 0) * 60 + parseFloat(tm[2] || 0);
		}
		tm = /^&[Tt=0]*([0-9\.]+)-([0-9\.]+)$/.exec(m[3]);
		if (tm) {
			ts = '' + tm[1] + '-' + tm[2];
		}
	}

	return [mtype, id, ts];
}


function eval_hash() {
	if (!window.hotkeys_attached) {
		window.hotkeys_attached = true;
		document.onkeydown = ahotkeys;
		window.onpopstate = treectl.onpopfun;
	}

	if (hash0 && window.og_fn) {
		var all = msel.getall(), mi;
		for (var a = 0; a < all.length; a++)
			if (og_fn == uricom_dec(vsplit(all[a].vp)[1].split('?')[0])) {
				mi = all[a];
				break;
			}

		var ch = !mi ? '' :
			img_re.exec(og_fn) ? 'g' :
			ebi('a' + mi.id) ? 'a' :
			'';

		hash0 = ch ? ('#' + ch + mi.id) : '';
	}

	var v = hash0;
	hash0 = null;
	if (!v)
		return;

	var media = scan_hash(v);
	if (media) {
		var mtype = media[0],
			id = media[1],
			ts = media[2];

		if (mtype == 'a') {
			if (!ts)
				return play(id, -1);

			return play(id, -1, ts);
		}

		if (mtype == 'g') {
			if (!thegrid.en)
				ebi('griden').click();

			var t = setInterval(function () {
				if (!thegrid.bbox)
					return;

				clearInterval(t);
				baguetteBox.urltime(ts);
				var im = QS('#ggrid a[ref="' + id + '"]');
				if (!im)
					return toast.warn(10, L.im_hnf);

				if (thegrid.sel)
					setTimeout(function () {
						thegrid.sel = true;
					}, 1);

				thegrid.sel = false;
				im.click();
				im.scrollIntoView();
			}, 50);
		}
	}

	if (v.startsWith('#q=')) {
		goto('search');
		var i = ebi('q_raw');
		i.value = uricom_dec(v.slice(3));
		return i.onkeydown({ 'key': 'Enter' });
	}

	if (v.startsWith('#v=')) {
		goto(v.slice(3));
		return;
	}

	if (v.startsWith("#m3u=")) {
		load_m3u(v.slice(5));
		return;
	}
}


(function () {
	var props = {};

	// a11y jump-to-content
	for (var a = 0; a < 2; a++)
		(function (a) {
			var d = mknod('a');
			d.setAttribute('href', '#');
			d.setAttribute('class', 'ayjump');
			d.innerHTML = a ? L.ay_path : L.ay_files;
			document.body.insertBefore(d, ebi('ops'));
			d.onclick = function (e) {
				ev(e);
				if (a)
					d = QS(treectl.hidden ? '#path a:nth-last-child(2)' : '#treeul a.hl');
				else
					d = QS(thegrid.en ? '#ggrid a' : '#files tbody tr[tabindex]');
				if (d)
					d.focus();
			};
		})(a);

	// account-info label
	var d = mknod('div', 'acc_info');
	document.body.insertBefore(d, ebi('ops'));

	// folder nav
	ebi('goh').parentElement.appendChild(mknod('span', null,
		'<a href="#" id="gop" tt="' + L.gop + '</a>/<a href="#" id="gou" tt="' + L.gou + '</a>/<a href="#" id="gon" tt="' + L.gon + '</a>'));
	ebi('gop').onclick = function () { tree_neigh(-1); }
	ebi('gon').onclick = function () { tree_neigh(1); }
	ebi('gou').onclick = function () { tree_up(true); }

	// show/hide scrollbars
	function setsb() {
		clmod(document.documentElement, 'noscroll', !props.sbars);
	}
	bcfg_bind(props, 'sbars', 'sbars', true, setsb);
	setsb();

	// compact media player
	function setacmp() {
		clmod(ebi('widget'), 'cmp', props.mcmp);
		pbar.onresize();
		vbar.onresize();
	}
	bcfg_bind(props, 'mcmp', 'au_compact', false, setacmp);
	setacmp();

	// toggle bup checksums
	ebi('uput').onchange = function() {
		QS('#op_bup input[name="act"]').value = this.checked ? 'uput' : 'bput';
	};
})();


function read_dsort(txt) {
	dnsort = dnsort ? 1 : 0;
	ENATSORT = NATSORT && (sread('nsort') || dnsort) == 1;
	clmod(ebi('nsort'), 'on', ENATSORT);
	try {
		var zt = (('' + txt).trim() || 'href').split(/,+/g);
		dsort = [];
		for (var a = 0; a < zt.length; a++) {
			var z = zt[a].trim(), n = 1, t = "";
			if (z.startsWith("-")) {
				z = z.slice(1);
				n = -1;
			}
			if (z == "sz" || z.indexOf('/.') + 1)
				t = "int";

			dsort.push([z, n, t]);
		}
	}
	catch (ex) {
		toast.warn(10, 'failed to apply default sort order [' + esc('' + txt) + ']:\n' + ex);
		dsort = [['href', 1, '']];
	}
}
read_dsort(dsort);


function getsort() {
	var ret = '',
		sopts = jread('fsort');

	sopts = sopts && sopts.length ? sopts : dsort;

	for (var a = 0; a < Math.min(hsortn, sopts.length); a++)
		ret += ',sort' + (sopts[a][1] < 0 ? '-' : '') + sopts[a][0];

	return ret;
}


function sortfiles(nodes) {
	if (!nodes.length)
		return nodes;

	var sopts = jread('fsort'),
		dir1st = sread('dir1st') !== '0';

	sopts = sopts && sopts.length ? sopts : jcp(dsort);

	try {
		var is_srch = false;
		if (nodes[0]['rp']) {
			is_srch = true;
			for (var b = 0, bb = nodes.length; b < bb; b++)
				nodes[b].ext = nodes[b].rp.split('.').pop();
			for (var b = 0; b < sopts.length; b++)
				if (sopts[b][0] == 'href')
					sopts[b][0] = 'rp';
		}
		for (var a = sopts.length - 1; a >= 0; a--) {
			var name = sopts[a][0], rev = sopts[a][1], typ = sopts[a][2];
			if (!name)
				continue;

			name = name.toLowerCase();

			if (name == 'ts')
				typ = 'int';

			if (name.indexOf('tags/') === 0) {
				name = name.slice(5);
				for (var b = 0, bb = nodes.length; b < bb; b++)
					nodes[b]._sv = nodes[b].tags[name];
			}
			else {
				for (var b = 0, bb = nodes.length; b < bb; b++) {
					var v = nodes[b][name];

					if ((v + '').indexOf('<a ') === 0)
						v = v.split('>')[1];
					else if (name == "href" && v)
						v = uricom_dec(v);

					nodes[b]._sv = v
				}
			}

			var onodes = nodes.map(function (x) { return x; });
			nodes.sort(function (n1, n2) {
				var v1 = n1._sv,
					v2 = n2._sv;

				if (v1 === undefined) {
					if (v2 === undefined) {
						return onodes.indexOf(n1) - onodes.indexOf(n2);
					}
					return -1 * rev;
				}
				if (v2 === undefined) return 1 * rev;

				var ret = rev * (typ == 'int' ? (v1 - v2) :
					ENATSORT ? NATSORT.compare(v1, v2) :
					v1.localeCompare(v2));

				if (ret === 0)
					ret = onodes.indexOf(n1) - onodes.indexOf(n2);

				return ret;
			});
		}
		for (var b = 0, bb = nodes.length; b < bb; b++) {
			delete nodes[b]._sv;
			if (is_srch)
				delete nodes[b].ext;
		}
		if (dir1st) {
			var r1 = [], r2 = [];
			for (var b = 0, bb = nodes.length; b < bb; b++)
				(nodes[b].href.split('?')[0].slice(-1) == '/' ? r1 : r2).push(nodes[b]);

			nodes = r1.concat(r2);
		}
	}
	catch (ex) {
		console.log("failed to apply sort config: " + ex);
		console.log("resetting fsort " + sread('fsort'));
		sdrop('fsort');
	}
	return nodes;
}


function fmt_ren(re, md, fmt) {
	var ptr = 0;
	function dive(stop_ch) {
		var ret = '', ng = 0;
		while (ptr < fmt.length) {
			var dbg = fmt.slice(ptr),
				ch = fmt[ptr++];

			if (ch == '\\') {
				ret += fmt[ptr++];
				continue;
			}

			if (ch == ')' || ch == ']' || ch == stop_ch)
				return [ng, ret];

			if (ch == '[') {
				var r2 = dive();
				if (r2[0] == 0)
					ret += r2[1];
			}
			else if (ch == '(') {
				var end = fmt.indexOf(')', ptr);
				if (end < 0)
					throw 'the ( was never closed: ' + fmt.slice(0, ptr);

				var arg = fmt.slice(ptr, end), v = null;
				ptr = end + 1;

				if (arg != parseInt(arg))
					v = md[arg];
				else {
					arg = parseInt(arg);
					if (arg >= re.length)
						throw 'matching group ' + arg + ' exceeds ' + (re.length - 0);

					v = re[arg];
				}

				if (v !== null && v !== undefined)
					ret += v;
				else
					ng++;
			}
			else if (ch == '$') {
				ch = fmt[ptr++];
				var end = fmt.indexOf('(', ptr);
				if (end < 0)
					throw 'no function name after the $ here: ' + fmt.slice(0, ptr);

				var fun = fmt.slice(ptr - 1, end);
				ptr = end + 1;

				if (fun == "lpad") {
					var str = dive(',')[1];
					var len = dive(',')[1];
					var chr = dive()[1];
					if (!len || !chr)
						throw 'invalid arguments to ' + fun;

					if (!str.length)
						ng += 1;

					while (str.length < len)
						str = chr + str;

					ret += str;
				}
				else if (fun == "rpad") {
					var str = dive(',')[1];
					var len = dive(',')[1];
					var chr = dive()[1];
					if (!len || !chr)
						throw 'invalid arguments to ' + fun;

					if (!str.length)
						ng += 1;

					while (str.length < len)
						str += chr;

					ret += str;
				}
				else throw 'function not implemented: "' + fun + '"';
			}
			else ret += ch;
		}
		return [ng, ret];
	}
	try {
		return [true, dive()[1]];
	}
	catch (ex) {
		return [false, ex];
	}
}


function fs_abrt() {
	toast.inf(30, L.fp_abrt);
	fileman.sn++;
	fileman.f.length = 0;
	var xhr = new XHR();
	xhr.open('POST', '/?fs_abrt=' + abrt_key, true);
	xhr.send();
}


var fileman = (function () {
	var bren = ebi('fren'),
		bdel = ebi('fdel'),
		bcut = ebi('fcut'),
		bcpy = ebi('fcpy'),
		bpst = ebi('fpst'),
		bshr = ebi('fshr'),
		t_paste,
		r = {};

	r.f = [];
	r.sn = 1;
	r.clip = null;
	try {
		r.bus = new BroadcastChannel("fileman_bus");
	}
	catch (ex) { }

	r.render = function () {
		if (r.clip === null) {
			r.clip = jread('fman_clip', []).slice(1);
			r.ccp = r.clip.length && r.clip[0] == '//c';
			if (r.ccp)
				r.clip.shift();
		}

		var sel = msel.getsel(),
			nsel = sel.length,
			enren = nsel,
			endel = nsel,
			encut = nsel,
			encpy = nsel,
			enpst = r.clip && r.clip.length,
			hren = !(have_mv && has(perms, 'write') && has(perms, 'move')),
			hdel = !(have_del && has(perms, 'delete')),
			hcut = !(have_mv && has(perms, 'move')),
			hpst = !(have_mv && has(perms, 'write')),
			hshr = !can_shr || !get_evpath().indexOf(have_shr);

		if (!(enren || endel || encut || enpst))
			hren = hdel = hcut = hpst = true;

		clmod(bren, 'en', enren);
		clmod(bdel, 'en', endel);
		clmod(bcut, 'en', encut);
		clmod(bcpy, 'en', encpy);
		clmod(bpst, 'en', enpst);
		clmod(bshr, 'en', 1);

		clmod(bren, 'hide', hren);
		clmod(bdel, 'hide', hdel);
		clmod(bcut, 'hide', hcut);
		clmod(bpst, 'hide', hpst);
		clmod(bshr, 'hide', hshr);

		clmod(ebi('wfm'), 'act', QS('#wfm a.en:not(.hide)'));
		clmod(ebi('wtoggle'), 'm3u', mpl.m3uen && (nsel || (mp && mp.au)));

		var wfs = ebi('wfs'), h = '';
		try {
			wfs.innerHTML = h = r.fsi(sel);
		}
		catch (ex) { }
		clmod(wfs, 'act', h);

		bpst.setAttribute('tt', L.ft_paste.format(r.clip.length));
		bshr.setAttribute('tt', nsel ? L.fs_ss : L.fs_sc);
	};

	r.fsi = function (sel) {
		if (!sel.length)
			return '';

		var lf = treectl.lsc.files,
			nf = 0,
			sz = 0,
			dur = 0,
			ntab = new Set();

		for (var a = 0; a < sel.length; a++)
			ntab.add(sel[a].vp.split('/').pop());

		for (var a = 0; a < lf.length; a++) {
			if (!ntab.has(lf[a].href.split('?')[0]))
				continue;

			var f = lf[a];
			nf++;
			sz += f.sz;
			if (f.tags && f.tags['.dur'])
				dur += f.tags['.dur']
		}

		if (!nf)
			return '';

		var ret = '{0}<br />{1}<small>F</small>'.format(humansize(sz), nf);

		if (dur)
			ret += ' ' + s2ms(dur);

		return ret;
	};

	r.share = function (e) {
		ev(e);

		var vp = uricom_dec(get_evpath()),
			sel = msel.getsel(),
			fns = [];

		for (var a = 0; a < sel.length; a++)
			fns.push(uricom_dec(noq_href(ebi(sel[a].id))));

		if (fns.length == 1 && fns[0].endsWith('/'))
			vp = fns.pop();

		for (var a = 0; a < fns.length; a++)
			if (fns[a].endsWith('/'))
				return toast.err(10, L.fs_just1d);

		var shui = ebi('shui');
		if (!shui) {
			shui = mknod('div', 'shui');
			document.body.appendChild(shui);
		}
		shui.style.display = 'block';

		var html = [
			'<div>',
			'<table>',
			'<tr><td colspan="2">',
			'<button id="sh_abrt">' + L.fs_abrt + '</button>',
			'<button id="sh_rand">' + L.fs_rand + '</button>',
			'<button id="sh_apply">' + L.fs_go + '</button>',
			'</td></tr>',
			'<tr><td>' + L.fs_name + '</td><td><input type="text" id="sh_k" ' + NOAC + ' placeholder="  ' + L.fs_pname + '" /></td></tr>',
			'<tr><td>' + L.fs_src + '</td><td><input type="text" id="sh_vp" ' + NOAC + ' readonly tt="' + L.fs_tsrc + '" /></td></tr>',
			'<tr><td>' + L.fs_pwd + '</td><td><input type="text" id="sh_pw" ' + NOAC + ' placeholder="  ' + L.fs_ppwd + '" /></td></tr>',
			'<tr><td>' + L.fs_exp + '</td><td class="exs">',
			'<input type="text" id="sh_exm" ' + NOAC + ' /> ' + L.fs_tmin + ' / ',
			'<input type="text" id="sh_exh" ' + NOAC + ' /> ' + L.fs_thrs + ' / ',
			'<input type="text" id="sh_exd" ' + NOAC + ' /> ' + L.fs_tdays + ' / ',
			'<button id="sh_noex">' + L.fs_never + '</button>',
			'</td></tr>',
			'<tr><td>perms</td><td class="sh_axs">',
		];
		for (var a = 0; a < perms.length; a++)
			if (!has(['admin', 'move'], perms[a]))
				html.push('<a href="#" class="tgl btn">' + perms[a] + '</a>');

		if (has(perms, 'write'))
			html.push('<a href="#" class="btn">write-only</a>');

		html.push('</td></tr></div');
		shui.innerHTML = html.join('\n');

		var sh_rand = ebi('sh_rand'),
			sh_abrt = ebi('sh_abrt'),
			sh_apply = ebi('sh_apply'),
			sh_noex = ebi('sh_noex'),
			exm = ebi('sh_exm'),
			exh = ebi('sh_exh'),
			exd = ebi('sh_exd'),
			sh_k = ebi('sh_k'),
			sh_vp = ebi('sh_vp'),
			sh_pw = ebi('sh_pw');

		function setexp(a, b) {
			a = parseFloat(a);
			if (!isNum(a))
				return;

			var v = a * b;
			swrite('fsh_exp', v);

			if (exm.value != v) exm.value = Math.round(v * 10) / 10; v /= 60;
			if (exh.value != v) exh.value = Math.round(v * 10) / 10; v /= 24;
			if (exd.value != v) exd.value = Math.round(v * 10) / 10;
		}
		function setdef() {
			setexp(icfg_get('fsh_exp', 60 * 24), 1);
		}
		setdef();

		exm.oninput = function () { setexp(this.value, 1); };
		exh.oninput = function () { setexp(this.value, 60); };
		exd.oninput = function () { setexp(this.value, 60 * 24); };
		exm.onfocus = exh.onfocus = exd.onfocus = function () {
			this.value = '';
		};
		sh_noex.onclick = function () {
			setexp(0, 1);
		};
		exm.onblur = exh.onblur = exd.onblur = setdef;

		exm.onkeydown = exh.onkeydown = exd.onkeydown =
		sh_k.onkeydown = sh_pw.onkeydown = function (e) {
			var kc = (e.key || e.code) + '';
			if (kc.endsWith('Enter'))
				sh_apply.click();
		};

		sh_abrt.onclick = function () {
			shui.parentNode.removeChild(shui);
		};
		sh_rand.onclick = function () {
			sh_k.value = randstr(12).replace(/l/g, 'n');
		};
		tt.att(shui);

		var pbtns = QSA('#shui .sh_axs a');
		for (var a = 0; a < pbtns.length; a++)
			pbtns[a].onclick = shspf;

		function shspf() {
			clmod(this, 'on', 't');
			if (this.textContent == 'write-only')
				for (var a = 0; a < pbtns.length; a++)
					clmod(pbtns[a], 'on', pbtns[a].textContent == 'write');
		}
		clmod(pbtns[0], 'on', 1);

		var vpt = vp;
		if (fns.length) {
			vpt = fns.length + ' files in ' + vp + '  '
			for (var a = 0; a < fns.length; a++)
				vpt += '「' + fns[a].split('/').pop() + '」';
		}
		sh_vp.value = vpt;

		sh_k.oninput = function (e) {
			var v = this.value,
				v2 = v.replace(/[^0-9a-zA-Z-]/g, '_');

			if (v != v2)
				this.value = v2;
		};

		function shr_cb() {
			toast.hide();
			var surl = this.responseText;
			if (this.status !== 201 || !/^created share:/.exec(surl)) {
				shui.style.display = 'block';
				var msg = unpre(surl);
				toast.err(9, msg);
				return;
			}
			surl = surl.slice(15).trim();
			var txt = esc(surl) + '<img class="b64" width="100" height="100" src="' + surl + '?qr" />';
			modal.confirm(txt + L.fs_ok, function() {
				cliptxt(surl, function () {
					toast.ok(2, L.clipped);
				});
			}, null);
		}

		sh_apply.onclick = function () {
			if (!sh_k.value)
				sh_rand.click();

			var plist = [];
			for (var a = 0; a < pbtns.length; a++)
				if (clgot(pbtns[a], 'on'))
					plist.push(pbtns[a].textContent);

			shui.style.display = 'none';
			toast.inf(30, L.fs_w8);

			var body = {
				"k": sh_k.value,
				"vp": fns.length ? fns : [sh_vp.value],
				"pw": sh_pw.value,
				"exp": exm.value,
				"perms": plist,
			};
			var xhr = new XHR();
			xhr.open('POST', SR + '/?share', true);
			xhr.setRequestHeader('Content-Type', 'text/plain');
			xhr.onload = xhr.onerror = shr_cb;
			xhr.send(JSON.stringify(body));
		};

		setTimeout(sh_pw.focus.bind(sh_pw), 1);
	};

	r.rename = function (e) {
		ev(e);
		var sel = msel.getsel(),
			all = msel.all;
		if (!sel.length)
			return toast.err(3, L.fr_emore);

		if (clgot(bren, 'hide'))
			return toast.err(3, L.fr_eperm);

		var f = [],
			sn = ++r.sn,
			base = vsplit(sel[0].vp)[0],
			s2d = {},
			mkeys;

		r.f = f;
		r.n_s = 1;
		r.n_d = 1;

		for (var a = 0; a < sel.length; a++) {
			s2d[a] = all.indexOf(sel[a]);

			var vp = sel[a].vp;
			if (vp.endsWith('/'))
				vp = vp.slice(0, -1);

			var vsp = vsplit(vp);
			if (base != vsp[0])
				return toast.err(0, esc('bug:\n' + base + '\n' + vsp[0]));

			var vars = ft2dict(ebi(sel[a].id).closest('tr'));
			mkeys = [".n.d", ".n.s"].concat(vars[1], vars[2]);

			var md = vars[0];
			md[".n.s"] = md[".n.d"] = 0;
			for (var k in md) {
				if (!md.hasOwnProperty(k))
					continue;

				md[k] = (md[k] + '').replace(/[\/\\]/g, '-');

				if (k.startsWith('.'))
					md[k.slice(1)] = md[k];
			}
			md.t = md.ext;
			md.date = md.ts;
			md.size = md.sz;

			f.push({
				"src": vp,
				"ofn": uricom_dec(vsp[1]),
				"md": vars[0],
				"ok": true
			});
		}

		var rui = ebi('rui');
		if (!rui) {
			rui = mknod('div', 'rui');
			document.body.appendChild(rui);
		}

		var html = sel.length > 1 ? ['<div>'] : [
			'<div>',
			'<button class="rn_dec" id="rn_dec_0" tt="' + L.frt_dec + '</button>',
			'//',
			'<button class="rn_reset" id="rn_reset_0" tt="' + L.frt_rst + '</button>'
		];

		html = html.concat([
			'<button id="rn_cancel" tt="' + L.frt_abrt + '</button>',
			'<button id="rn_apply">✅ ' + L.frb_apply + '</button>',
			'<a id="rn_adv" class="tgl btn" href="#" tt="' + L.fr_adv + '</a>',
			'<a id="rn_case" class="tgl btn" href="#" tt="' + L.fr_case + '</a>',
			'<a id="rn_win" class="tgl btn" href="#" tt="' + L.fr_win + '</a>',
			'<a id="rn_slash" class="tgl btn" href="#" tt="' + L.fr_slash + '</a>',
			'</div>',
			'<div id="rn_vadv"><table>',
			'<tr><td>regex</td><td><input type="text" id="rn_re" ' + NOAC + ' tt="' + L.fr_re + '" placeholder="^[0-9]+[\\. ]+(.*) - (.*)" /></td></tr>',
			'<tr><td>format</td><td><input type="text" id="rn_fmt" ' + NOAC + ' tt="' + L.fr_fmt + '" placeholder="[(artist) - ](title).(ext)" /></td></tr>',
			'<tr><td>preset</td><td><select id="rn_pre"></select>',
			'<tr><td>num0</td><td>',
			'<code>n.d=</code><input type="text" id="rn_n_d" placeholder="1" ' + NOAC + ' /> &nbsp;',
			'<code>n.s=</code><input type="text" id="rn_n_s" placeholder="1" ' + NOAC + ' />',
			'</td></tr>',
			'<button id="rn_pdel">❌ ' + L.fr_pdel + '</button>',
			'<button id="rn_pnew">💾 ' + L.fr_pnew + '</button>',
			'</td></tr>',
			'</table></div>'
		]);

		var cheap = f.length > 500,
			t_rst = L.frt_rst.split('>').pop();

		if (sel.length == 1)
			html.push(
				'<div><table id="rn_f">\n' +
				'<tr><td>old:</td><td><input type="text" id="rn_old_0" readonly /></td></tr>\n' +
				'<tr><td>new:</td><td><input type="text" id="rn_new_0" /></td></tr>');
		else {
			html.push(
				'<div><table id="rn_f" class="m">' +
				'<tr><td></td><td>' + L.fr_lnew + '</td><td>' + L.fr_lold + '</td></tr>');
			for (var a = 0; a < f.length; a++)
				html.push(
					'<tr><td>' +
					(cheap ? '</td>' :
						'<button class="rn_dec" id="rn_dec_' + a + '">decode</button>' +
						'<button class="rn_reset" id="rn_reset_' + a + '">' + t_rst + '</button></td>') +
					'<td><input type="text" id="rn_new_' + a + '" /></td>' +
					'<td><input type="text" id="rn_old_' + a + '" readonly /></td></tr>');
		}
		html.push('</table></div>');

		if (sel.length == 1) {
			html.push('<div><p style="margin:.6em 0">' + L.fr_tags + '</p><table>');
			for (var a = 0; a < mkeys.length; a++)
				html.push('<tr><td>' + esc(mkeys[a]) + '</td><td><input type="text" readonly value="' + esc(f[0].md[mkeys[a]]) + '" /></td></tr>');

			html.push('</table></div>');
		}

		rui.innerHTML = html.join('\n');
		for (var a = 0; a < f.length; a++) {
			f[a].iold = ebi('rn_old_' + a);
			f[a].inew = ebi('rn_new_' + a);
			f[a].inew.value = f[a].iold.value = f[a].ofn;

			if (!cheap)
				(function (a) {
					f[a].inew.onkeydown = function (e) {
						rn_ok(a, true);
						var kc = (e.key || e.code) + '';
						if (kc.endsWith('Enter'))
							return rn_apply();
					};
					ebi('rn_dec_' + a).onclick = function (e) {
						ev(e);
						f[a].inew.value = uricom_dec(f[a].inew.value);
					};
					ebi('rn_reset_' + a).onclick = function (e) {
						ev(e);
						rn_reset(a);
					};
				})(a);
		}
		rn_reset(0);
		tt.att(rui);

		function sadv() {
			ebi('rn_vadv').style.display = ebi('rn_case').style.display = r.adv ? '' : 'none';
		}
		bcfg_bind(r, 'adv', 'rn_adv', false, sadv);
		bcfg_bind(r, 'cs', 'rn_case', false);
		bcfg_bind(r, 'win', 'rn_win', true);
		bcfg_bind(r, 'slash', 'rn_slash', true);
		sadv();

		function rn_ok(n, ok) {
			f[n].ok = ok;
			clmod(f[n].inew.closest('tr'), 'err', !ok);
		}

		function rn_reset(n) {
			f[n].inew.value = f[n].iold.value = f[n].ofn;
			f[n].inew.focus();
			f[n].inew.setSelectionRange(0, f[n].inew.value.lastIndexOf('.'), "forward");
		}
		function rn_cancel(e) {
			ev(e);
			rui.parentNode.removeChild(rui);
		}

		ebi('rn_cancel').onclick = rn_cancel;
		ebi('rn_apply').onclick = rn_apply;

		var ire = ebi('rn_re'),
			ifmt = ebi('rn_fmt'),
			ipre = ebi('rn_pre'),
			idel = ebi('rn_pdel'),
			inew = ebi('rn_pnew'),
			defp = '$lpad((tn),2,0). [(artist) - ](title).(ext)';

		ire.value = sread('cpp_rn_re') || '';
		ifmt.value = sread('cpp_rn_fmt') || '';

		var presets = {};
		presets[defp] = ['', defp];
		presets = jread("rn_pre", presets);

		function spresets() {
			var keys = Object.keys(presets), o;
			keys.sort();
			ipre.innerHTML = '<option value=""></option>';
			for (var a = 0; a < keys.length; a++) {
				o = mknod('option');
				o.setAttribute('value', keys[a]);
				o.textContent = keys[a];
				ipre.appendChild(o);
			}
		}
		inew.onclick = function (e) {
			ev(e);
			modal.prompt(L.fr_pname, ifmt.value, function (name) {
				if (!name)
					return toast.warn(3, L.fr_aborted);

				presets[name] = [ire.value, ifmt.value];
				jwrite('rn_pre', presets);
				spresets();
				ipre.value = name;
			});
		};
		idel.onclick = function (e) {
			ev(e);
			delete presets[ipre.value];
			jwrite('rn_pre', presets);
			spresets();
		};
		ipre.oninput = function () {
			var cfg = presets[ipre.value];
			if (cfg) {
				ire.value = cfg[0];
				ifmt.value = cfg[1];
			}
			ifmt.oninput();
		};
		spresets();

		ebi('rn_n_s').oninput = function () {
			r.n_s = parseInt(this.value || '1');
			ifmt.oninput();
		};
		ebi('rn_n_d').oninput = function () {
			r.n_d = parseInt(this.value || '1');
			ifmt.oninput();
		};

		ire.onkeydown = ifmt.onkeydown = function (e) {
			var k = (e.key || e.code) + '';

			if (k == 'Escape' || k == 'Esc')
				return rn_cancel();

			if (k.endsWith('Enter'))
				return rn_apply();
		};

		ire.oninput = ifmt.oninput = function (e) {
			var ptn = ire.value,
				fmt = ifmt.value,
				re = null;

			if (!fmt)
				return;

			try {
				if (ptn)
					re = new RegExp(ptn, r.cs ? 'i' : '');
			}
			catch (ex) {
				return toast.err(5, esc('invalid regex:\n' + ex));
			}
			toast.hide();

			for (var a = 0; a < f.length; a++) {
				var m = re ? re.exec(f[a].ofn) : null,
					d = f[a].md,
					ok, txt = '';

				d[".n.s"] = d["n.s"] = '' + (r.n_s + a);
				d[".n.d"] = d["n.d"] = '' + (r.n_d + s2d[a]);

				if (re && !m) {
					txt = 'regex did not match';
					ok = false;
				}
				else {
					var ret = fmt_ren(m, d, fmt);
					ok = ret[0];
					txt = ret[1];
				}
				rn_ok(a, ok);
				f[a].inew.value = (ok ? '' : 'ERROR: ') + txt;
			}
		};

		function rn_apply(e) {
			ev(e);
			swrite('cpp_rn_re', ire.value);
			swrite('cpp_rn_fmt', ifmt.value);
			if (r.win || r.slash) {
				var changed = 0;
				for (var a = 0; a < f.length; a++) {
					var ov = f[a].inew.value,
						nv = namesan(ov, r.win, r.slash);

					if (ov != nv) {
						f[a].inew.value = nv;
						changed++;
					}
				}
				if (changed)
					return modal.confirm(L.fr_nchg.format(changed), rn_apply_loop, null);
			}
			rn_apply_loop();
		}

		function rn_apply_loop() {
			while (f.length && (!f[0].ok || f[0].ofn == f[0].inew.value))
				f.shift();

			if (!f.length) {
				toast.ok(2, 'rename OK');
				treectl.goto();
				return rn_cancel();
			}

			var msg = esc(L.fr_busy.format(f.length, f[0].ofn));
			msg += '\n<a id="fs_abrt" class="btn" href="#" onclick="fs_abrt()">' + L.fs_abrt + '</a>';
			toast.show('inf r', 0, msg);
			var dst = base + uricom_enc(f[0].inew.value, false);

			function rename_cb() {
				if (this.status !== 201) {
					var msg = unpre(this.responseText);
					toast.err(9, L.fr_efail + msg);
					return;
				}
				if (r.sn != sn)
					return modal.confirm('WARNING: the rename was aborted');

				f.shift().inew.value = '( OK )';
				return rn_apply_loop();
			}

			abrt_key = randstr(9);

			var xhr = new XHR();
			xhr.open('POST', f[0].src + '?move=' + dst + '&akey=' + abrt_key, true);
			xhr.onload = xhr.onerror = rename_cb;
			xhr.send();
		}
	};

	r.delete = function (e) {
		var sel = msel.getsel(),
			sn = ++r.sn,
			vps = [];

		for (var a = 0; a < sel.length; a++)
			vps.push(sel[a].vp);

		if (!sel.length)
			return toast.err(3, L.fd_emore);

		ev(e);

		if (clgot(bdel, 'hide'))
			return toast.err(3, L.fd_eperm);

		function deleter(err) {
			var xhr = new XHR(),
				vp = vps.shift();

			if (!vp) {
				if (err !== 'xbd')
					toast.ok(2, L.fd_ok);

				treectl.goto();
				return;
			}
			toast.show('inf r', 0, esc(L.fd_busy.format(vps.length + 1, vp)), 'r');

			xhr.open('POST', vp + '?delete', true);
			xhr.onload = xhr.onerror = delete_cb;
			xhr.send();
		}
		function delete_cb() {
			if (this.status !== 200) {
				var msg = unpre(this.responseText);
				toast.err(9, L.fd_err + msg);
				return;
			}
			if (r.sn != sn)
				return modal.confirm('WARNING: the delete was aborted');

			if (this.responseText.indexOf('deleted 0 files (and 0') + 1) {
				toast.err(9, L.fd_none);
				return deleter('xbd');
			}
			deleter();
		}

		var asks = r.qdel ? 1 : 2;
		if (dqdel === 0)
			asks -= 1;

		if (!asks)
			return deleter();

		modal.confirm('<h6 style="color:#900">' + L.danger + '</h6>\n<b>' + L.fd_warn1.format(vps.length) + '</b><ul>' + uricom_adec(vps, true).join('') + '</ul>', function () {
			if (asks === 1)
				return deleter();
			modal.confirm(L.fd_warn2, deleter, null);
		}, null);
	};

	r.cut = function (e) {
		var sel = msel.getsel(),
			stamp = Date.now(),
			vps = [stamp];

		if (!sel.length)
			return toast.err(3, L.fc_emore);

		ev(e);

		if (clgot(bcut, 'hide'))
			return toast.err(3, L.fc_eperm);

		var els = [], griden = thegrid.en;
		for (var a = 0; a < sel.length; a++) {
			vps.push(sel[a].vp);
			if (sel.length < 100)
				try {
					if (griden)
						els.push(QS('#ggrid>a[ref="' + sel[a].id + '"]'));
					else
						els.push(ebi(sel[a].id).closest('tr'));

					clmod(els[a], 'fcut');
				}
				catch (ex) { }
		}

		setTimeout(function () {
			try {
				for (var a = 0; a < els.length; a++)
					clmod(els[a], 'fcut', 1);
			}
			catch (ex) { }
		}, 1);

		r.ccp = false;
		r.clip = vps.slice(1);

		try {
			vps = JSON.stringify(vps);
			if (vps.length > 1024 * 1024)
				throw 'a';

			swrite('fman_clip', vps);
			r.tx(stamp);
			if (sel.length)
				toast.inf(1.5, L.fc_ok.format(sel.length));
		}
		catch (ex) {
			toast.warn(30, L.fc_warn.format(sel.length));
		}
	};

	r.cpy = function (e) {
		var sel = msel.getsel(),
			stamp = Date.now(),
			vps = [stamp, '//c'];

		if (!sel.length)
			return toast.err(3, L.fcp_emore);

		ev(e);

		var els = [], griden = thegrid.en;
		for (var a = 0; a < sel.length; a++) {
			vps.push(sel[a].vp);
			if (sel.length < 100)
				try {
					if (griden)
						els.push(QS('#ggrid>a[ref="' + sel[a].id + '"]'));
					else
						els.push(ebi(sel[a].id).closest('tr'));

					clmod(els[a], 'fcut');
				}
				catch (ex) { }
		}

		setTimeout(function () {
			try {
				for (var a = 0; a < els.length; a++)
					clmod(els[a], 'fcut', 1);
			}
			catch (ex) { }
		}, 1);

		if (vps.length < 3)
			vps.pop();

		r.ccp = true;
		r.clip = vps.slice(2);

		try {
			vps = JSON.stringify(vps);
			if (vps.length > 1024 * 1024)
				throw 'a';

			swrite('fman_clip', vps);
			r.tx(stamp);
			if (sel.length)
				toast.inf(1.5, L.fcc_ok.format(sel.length));
		}
		catch (ex) {
			toast.warn(30, L.fcc_warn.format(sel.length));
		}
	};

	document.onpaste = function (e) {
		var xfer = e.clipboardData || window.clipboardData;
		if (!xfer || !xfer.files || !xfer.files.length)
			return;

		var files = [];
		for (var a = 0, aa = xfer.files.length; a < aa; a++)
			files.push(xfer.files[a]);

		clearTimeout(t_paste);

		if (!r.clip.length)
			return r.clip_up(files);

		var src = r.clip.length == 1 ? r.clip[0] : vsplit(r.clip[0])[0],
			msg = (r.ccp ? L.fcp_both_m : L.fp_both_m).format(r.clip.length, src, files.length);

		modal.confirm(msg, r.paste, function () { r.clip_up(files); }, null, (r.ccp ? L.fcp_both_b : L.fp_both_b));
	};

	r.clip_up = function (files) {
		goto_up2k();
		var good = [], nil = [], bad = [];
		for (var a = 0, aa = files.length; a < aa; a++) {
			var fobj = files[a], dst = good;
			try {
				if (fobj.size < 1)
					dst = nil;
			}
			catch (ex) {
				dst = bad;
			}
			dst.push([fobj, fobj.name]);
		}
		var doit = function (is_img) {
			jwrite('fman_clip', [Date.now()]);
			r.clip = [];

			var x = up2k.uc.ask_up;
			if (is_img)
				up2k.uc.ask_up = false;

			up2k.gotallfiles[0](good, nil, bad, up2k.gotallfiles.slice(1));
			up2k.uc.ask_up = x;
		};
		if (good.length != 1)
			return doit();

		var fn = good[0][1],
			ofs = fn.lastIndexOf('.');

		// stop linux-chrome from adding the fs-path into the <input>
		setTimeout(function () {
			modal.prompt(L.fp_name, fn, function (v) {
				good[0][1] = v;
				doit(true);
			}, null, null, 0, ofs > 0 ? ofs : undefined);
		}, 1);
	};

	r.d_paste = function () {
		// gets called before onpaste; defer
		clearTimeout(t_paste);
		t_paste = setTimeout(r.paste, 50);
	};

	r.paste = function () {
		if (!r.clip.length)
			return toast.err(5, L.fp_ecut);

		if (clgot(bpst, 'hide'))
			return toast.err(3, L.fp_eperm);

		var html = [
				'<div>',
				'<button id="rn_cancel" tt="' + L.frt_abrt + '</button>',
				'<button id="rn_apply">✅ ' + L.fp_apply + '</button>',
				' &nbsp; src: ' + esc(r.clip[0].replace(/[^/]+$/, '')),
				'</div>',
				'<p id="cnmt"></p>',
				'<div><table id="rn_f" class="m">',
				'<tr><td>' + L.fr_lnew + '</td><td>' + L.fr_lold + '</td></tr>',
			],
			sn = ++r.sn,
			ui = false,
			f = [],
			indir = [],
			srcdir = vsplit(r.clip[0])[0],
			links = QSA('#files tbody td:nth-child(2) a');

		r.f = f;

		for (var a = 0, aa = links.length; a < aa; a++)
			indir.push(uricom_dec(vsplit(noq_href(links[a]))[1]));

		for (var a = 0; a < r.clip.length; a++) {
			var t = {
				'ok': true,
				'src': r.clip[a],
				'dst': uricom_dec(r.clip[a].split('/').pop()),
			};
			f.push(t);

			for (var b = 0; b < indir.length; b++)
				if (t.dst == indir[b]) {
					t.ok = false;
					ui = true;
				}

			html.push('<tr' + (!t.ok ? ' class="ng"' : '') + '><td><input type="text" id="rn_new_' + a + '" value="' + esc(t.dst) + '" /></td><td><input type="text" id="rn_old_' + a + '" value="' + esc(t.dst) + '" readonly /></td></tr>');
		}

		function paster() {
			var t = f.shift();
			if (!t) {
				toast.ok(2, r.ccp ? L.fcp_ok : L.fp_ok);
				treectl.goto();
				r.tx(srcdir);
				return;
			}
			if (!t.dst)
				return paster();

			var msg = esc((r.ccp ? L.fcp_busy : L.fp_busy).format(f.length + 1, uricom_dec(t.src)));
			msg += '\n<a id="fs_abrt" class="btn" href="#" onclick="fs_abrt()">' + L.fs_abrt + '</a>';
			toast.show('inf r', 0, msg);

			var xhr = new XHR(),
				act = r.ccp ? '?copy=' : '?move=',
				dst = get_evpath() + uricom_enc(t.dst);

			abrt_key = randstr(9);

			xhr.open('POST', t.src + act + dst + '&akey=' + abrt_key, true);
			xhr.onload = xhr.onerror = paste_cb;
			xhr.send();
		}
		function paste_cb() {
			if (this.status !== 201) {
				var msg = unpre(this.responseText);
				toast.err(9, (r.ccp ? L.fcp_err : L.fp_err) + msg);
				return;
			}
			if (r.sn != sn)
				return modal.confirm('WARNING: the paste was aborted');

			paster();
		}
		function okgo() {
			paster();
			jwrite('fman_clip', [Date.now()]);
		}

		if (!ui) {
			var src = [];
			for (var a = 0; a < f.length; a++)
				src.push(f[a].src);

			return modal.confirm((r.ccp ? L.fcp_confirm : L.fp_confirm).format(f.length) + '<ul>' + uricom_adec(src, true).join('') + '</ul>', okgo, null);
		}

		var rui = ebi('rui');
		if (!rui) {
			rui = mknod('div', 'rui');
			document.body.appendChild(rui);
		}
		html.push('</table>');
		rui.innerHTML = html.join('\n');
		tt.att(rui);

		function rn_apply(e) {
			for (var a = 0; a < f.length; a++)
				if (!f[a].ok) {
					toast.err(30, L.fp_emore);
					return setcnmt(true);
				}
			rn_cancel(e);
			okgo();
		}
		function rn_cancel(e) {
			ev(e);
			rui.parentNode.removeChild(rui);
		}
		ebi('rn_cancel').onclick = rn_cancel;
		ebi('rn_apply').onclick = rn_apply;

		var first_bad = 0;
		function setcnmt(sel) {
			var nbad = 0;
			for (var a = 0; a < f.length; a++) {
				if (f[a].ok)
					continue;
				if (!nbad)
					first_bad = a;
				nbad += 1;
			}
			ebi('cnmt').innerHTML = (r.ccp ? L.fcp_ename : L.fp_ename).format(nbad);
			if (sel && nbad) {
				var el = ebi('rn_new_' + first_bad);
				el.focus();
				el.setSelectionRange(0, el.value.lastIndexOf('.'), "forward");
			}
		}
		setcnmt(true);

		for (var a = 0; a < f.length; a++)
			(function (a) {
				var inew = ebi('rn_new_' + a);
				inew.onkeydown = function (e) {
					if (((e.key || e.code) + '').endsWith('Enter'))
						return rn_apply();
				};
				inew.oninput = function (e) {
					f[a].dst = this.value;
					f[a].ok = true;
					if (f[a].dst)
						for (var b = 0; b < indir.length; b++)
							if (indir[b] == this.value)
								f[a].ok = false;
					clmod(this.closest('tr'), 'ng', !f[a].ok);
					setcnmt();
				};
			})(a);
	}

	function onmsg(msg) {
		r.clip = null;
		var n = parseInt('' + msg), tries = 0;
		var fun = function () {
			if (n == msg && n > 1 && r.clip === null) {
				var fc = jread('fman_clip', []);
				if (!fc || !fc.length || fc[0] != n) {
					if (++tries > 10)
						return modal.alert(L.fp_etab);

					return setTimeout(fun, 100);
				}
			}
			r.render();
			if (msg == get_evpath())
				treectl.goto(msg);
		};
		fun();
	}

	if (r.bus)
		r.bus.onmessage = function (e) {
			onmsg(e ? e.data : 1)
		};

	r.tx = function (msg) {
		if (!r.bus)
			return onmsg(msg);

		r.bus.postMessage(msg);
		r.bus.onmessage();
	};

	bcfg_bind(r, 'qdel', 'qdel', dqdel == 1);

	bren.onclick = r.rename;
	bdel.onclick = r.delete;
	bcut.onclick = r.cut;
	bcpy.onclick = r.cpy;
	bpst.onclick = r.paste;
	bshr.onclick = r.share;

	return r;
})();


var showfile = (function () {
	var r = {
		'nrend': 0,
	};
	r.map = {
		'.ahk': 'autohotkey',
		'.bas': 'basic',
		'.bat': 'batch',
		'.cxx': 'cpp',
		'.diz': 'ans',
		'.ex': 'elixir',
		'.exs': 'elixir',
		'.frag': 'glsl',
		'.h': 'c',
		'.hpp': 'cpp',
		'.htm': 'html',
		'.hxx': 'cpp',
		'.log': 'ans',
		'.m': 'matlab',
		'.moon': 'moonscript',
		'.patch': 'diff',
		'.ps1': 'powershell',
		'.psm1': 'powershell',
		'.pl': 'perl',
		'.rs': 'rust',
		'.sh': 'bash',
		'.service': 'systemd',
		'.vb': 'vbnet',
		'.v': 'verilog',
		'.vert': 'glsl',
		'.vh': 'verilog',
		'.yml': 'yaml'
	};
	r.nmap = {
		'cmakelists.txt': 'cmake',
		'dockerfile': 'docker'
	};
	var x = txt_ext + ' ans c cfg conf cpp cs css diff glsl go html ini java js json jsx kt kts latex less lisp lua makefile md nim py r rss rb ruby sass scss sql svg swift tex toml ts vhdl xml yaml zig';
	x = x.split(/ +/g);
	for (var a = 0; a < x.length; a++)
		r.map["." + x[a]] = x[a];

	r.sname = function (srch) {
		return srch.split(/[?&]doc=/)[1].split('&')[0];
	};

	if (window.og_fn) {
		var ext = og_fn.split(/\./g).pop();
		if (r.map['.' + ext])
			hist_replace(get_evpath() + '?doc=' + og_fn);
	}

	window.Prism = { 'manual': true };
	var em = QS('#bdoc>pre');
	if (em)
		em = [r.sname(location.search), location.hash, em.textContent];
	else {
		var m = /[?&]doc=([^&]+)/.exec(location.search);
		if (m) {
			setTimeout(function () {
				r.show(uricom_dec(m[1]), true);
			}, 1);
		}
	}

	r.setstyle = function () {
		if (window.no_prism)
			return;

		qsr('#prism_css');
		var el = mknod('link', 'prism_css');
		el.rel = 'stylesheet';
		el.href = SR + '/.cpr/deps/prism' + (light ? '' : 'd') + '.css?_=' + TS;
		document.head.appendChild(el);
	};

	r.active = function () {
		return !!/[?&]doc=/.exec(location.search);
	};

	r.getlang = function (fn) {
		fn = fn.toLowerCase();
		var ext = fn.slice(fn.lastIndexOf('.'));
		return r.map[ext] || r.nmap[fn];
	}

	r.addlinks = function () {
		r.files = [];
		var links = msel.getall();
		for (var a = 0; a < links.length; a++) {
			var link = links[a],
				fn = link.vp.split('/').pop(),
				lang = r.getlang(fn);

			if (!lang)
				continue;

			r.files.push({ 'id': link.id, 'name': uricom_dec(fn) });

			var ah = ebi(link.id),
				td = ah.closest('tr').getElementsByTagName('td')[0];

			if (ah.textContent.endsWith('/'))
				continue;

			if (lang == 'ts' || (lang == 'md' && td.textContent != '-'))
				continue;

			td.innerHTML = '<a href="#" id="t' +
				link.id + '" class="doc bri" hl="' +
				link.id + '" rel="nofollow">-txt-</a>';

			td.getElementsByTagName('a')[0].setAttribute('href', '?doc=' + fn);
		}
		r.mktree();
		if (em) {
			if (r.taildoc)
				r.show(em[0], true);
			else
				render(em);
			em = null;
		}
	};

	r.tail = function (url, no_push) {
		r.abrt = new AbortController();
		widget.setvis();
		render([url, '', ''], no_push);
		var me = r.tail_id = Date.now(),
			wfp = ebi('wfp'),
			edoc = ebi('doc'),
			txt = '';

		url = addq(url, 'tail=-' + r.tailnb);
		fetch(url, {'signal': r.abrt.signal}).then(function(rsp) {
			var ro = rsp.body.pipeThrough(
				new TextDecoderStream('utf-8', {'fatal': false}),
				{'signal': r.abrt.signal}).getReader();

			var rf = function() {
				ro.read().then(function(v) {
					if (r.tail_id != me)
						return;
					var vt = v.done ? '\n*** lost connection to copyparty ***' : v.value;
					if (vt == '\x00')
						return rf();
					txt += vt;
					var ofs = txt.length - r.tailnb;
					if (ofs > 0) {
						var ofs2 = txt.indexOf('\n', ofs);
						if (ofs2 >= ofs && ofs - ofs2 < 512)
							ofs = ofs2;
						txt = txt.slice(ofs);
					}
					var html = esc(txt);
					if (r.tailansi)
						html = r.ansify(html);
					edoc.innerHTML = html;
					if (r.tail2end)
						window.scrollTo(0, wfp.offsetTop - window.innerHeight);
					if (!v.done)
						rf();
				});
			};
			if (r.tail_id == me)
				rf();
		});
	};

	r.untail = function () {
		if (!r.abrt)
			return;
		r.abrt.abort();
		r.abrt = null;
		r.tail_id = -1;
		widget.setvis();
	};

	r.show = function (url, no_push) {
		r.untail();
		var xhr = new XHR(),
			m = /[?&](k=[^&#]+)/.exec(url);

		url = url.split('?')[0] + (m ? '?' + m[1] : '');
		assert_vp(url);
		if (r.taildoc)
			return r.tail(url, no_push);

		xhr.url = url;
		xhr.fname = uricom_dec(url.split('/').pop());
		xhr.no_push = no_push;
		xhr.ts = Date.now();
		xhr.open('GET', url, true);
		xhr.onprogress = loading;
		xhr.onload = xhr.onerror = load_cb;
		xhr.send();
	};

	function loading(e) {
		if (e.total < 1024 * 256)
			return;

		var m = L.tv_load.format(
			esc(this.fname),
			f2f(e.loaded * 100 / e.total, 1),
			f2f(e.loaded / 1024 / 1024, 1),
			f2f(e.total / 1024 / 1024, 1))

		if (!this.toasted) {
			this.toasted = 1;
			return toast.inf(573, m);
		}
		ebi('toastb').innerHTML = lf2br(m);
	}

	function load_cb(e) {
		if (this.toasted)
			toast.hide();

		if (!xhrchk(this, L.tv_xe1, L.tv_xe2))
			return;

		render([this.url, '', this.responseText], this.no_push);
	}

	function render(doc, no_push) {
		r.q = null;
		r.nrend++;
		var url = r.url = doc[0],
			lnh = doc[1],
			txt = doc[2],
			name = url.split('?')[0].split('/').pop(),
			tname = uricom_dec(name),
			lang = r.getlang(name),
			is_md = lang == 'md';

		ebi('files').style.display = ebi('gfiles').style.display = ebi('lazy').style.display = ebi('pro').style.display = ebi('epi').style.display = 'none';
		ebi('dldoc').setAttribute('href', url);
		ebi('editdoc').setAttribute('href', addq(url, 'edit'));
		ebi('editdoc').style.display = (has(perms, 'write') && (is_md || has(perms, 'delete'))) ? '' : 'none';

		var wr = ebi('bdoc'),
			nrend = r.nrend,
			defer = !Prism.highlightElement;

		var fun = function (el) {
			if (r.nrend != nrend)
				return;

			try {
				if (lnh.slice(0, 5) == '#doc.')
					sethash(lnh.slice(1));

				el = el || QS('#doc>code');
				Prism.highlightElement(el);
				if (el.className == 'language-ans' || (!lang && /\x1b\[[0-9;]{0,16}m/.exec(txt.slice(0, 4096))))
					el.innerHTML = r.ansify(el.innerHTML);
			}
			catch (ex) { }
		}

		var skip_prism = !txt || txt.length > 1024 * 256;
		if (skip_prism) {
			fun = function (el) { };
			is_md = false;
		}

		qsr('#doc');
		var el = mknod('pre', 'doc');
		el.setAttribute('tabindex', '0');
		clmod(ebi('wrap'), 'doc', !is_md);
		if (is_md) {
			show_md(txt, name, el);
		}
		else {
			el.textContent = txt;
			el.innerHTML = '<code>' + el.innerHTML + '</code>';
			if (!window.no_prism && !skip_prism) {
				if ((lang == 'conf' || lang == 'cfg') && ('\n' + txt).indexOf('\n# -*- mode: yaml -*-') + 1)
					lang = 'yaml';

				el.className = 'prism linkable-line-numbers line-numbers language-' + lang;
				if (!defer)
					fun(el.firstChild);
				else
					import_js(SR + '/.cpr/deps/prism.js', function () { fun(); });
			}
			if (!txt && r.wrap)
				el.className = 'wrap';
		}

		wr.appendChild(el);
		wr.style.display = '';
		set_tabindex();

		wintitle(tname + ' \u2014 ');
		document.documentElement.scrollTop = 0;
		var hfun = no_push ? hist_replace : hist_push;
		hfun(get_evpath() + '?doc=' + name);  // can't dk: server wants dk and js needs fk

		qsr('#docname');
		el = mknod('span', 'docname');
		el.textContent = tname;
		ebi('path').appendChild(el);

		r.updtree();
		treectl.textmode(true);
		tree_scrollto();
	}

	r.ansify = function (html) {
		var ctab = (light ?
			'bfbfbf d30253 497600 b96900 006fbb a50097 288276 2d2d2d 9f9f9f 943b55 3a5600 7f4f00 00507d 683794 004343 000000' :
			'404040 f03669 b8e346 ffa402 02a2ff f65be3 3da698 d2d2d2 606060 c75b79 c8e37e ffbe4a 71cbff b67fe3 9cf0ed ffffff').split(/ /g),
			src = html.split(/\x1b\[/g),
			out = ['<span>'], fg = 7, bg = null, bfg = 0, bbg = 0, inv = 0, bold = 0;

		for (var a = 0; a < src.length; a++) {
			var m = /^([0-9;]+)m/.exec(src[a]);
			if (!m) {
				if (a)
					out.push('\x1b[');

				out.push(src[a]);
				continue;
			}

			var cs = m[1].split(/;/g),
				txt = src[a].slice(m[1].length + 1);

			for (var b = 0; b < cs.length; b++) {
				var c = parseInt(cs[b]);
				if (c == 0) {
					fg = 7;
					bg = null;
					bfg = bbg = bold = inv = 0;
				}
				if (c == 1) bfg = bold = 1;
				if (c == 7) inv = 1;
				if (c == 22) bfg = bold = 0;
				if (c == 27) inv = 0;
				if (c >= 30 && c <= 37) fg = c - 30;
				if (c >= 40 && c <= 47) bg = c - 40;
				if (c >= 90 && c <= 97) {
					fg = c - 90;
					bfg = 1;
				}
				if (c >= 100 && c <= 107) {
					bg = c - 100;
					bbg = 1;
				}
			}

			var cfg = fg, cbg = bg;
			if (inv) {
				cbg = fg;
				cfg = bg || 0;
			}

			var s = '</span><span style="color:#' + ctab[cfg + bfg * 8];
			if (cbg !== null)
				s += ';background:#' + ctab[cbg + bbg * 8];
			if (bold)
				s += ';font-weight:bold';

			out.push(s + '">' + txt);
		}
		return out.join('');
	};

	r.mktree = function () {
		var top = get_evpath().slice(SR.length),
			crumbs = linksplit(top).join('<span>/</span>'),
			html = ['<li class="bn">' + L.tv_lst + '<br />' + crumbs + '</li>'];
		for (var a = 0; a < r.files.length; a++) {
			var file = r.files[a];
			html.push('<li><a href="?doc=' +
				uricom_enc(file.name) + '" hl="' + file.id +
				'">' + esc(file.name) + '</a>');
		}
		ebi('docul').innerHTML = html.join('\n');
	};

	r.updtree = function () {
		var fn = QS('#path span:last-child'),
			lis = QSA('#docul li a'),
			sels = msel.getsel(),
			actsel = false;

		fn = fn ? fn.textContent : '';
		for (var a = 0, aa = lis.length; a < aa; a++) {
			var lin = lis[a].textContent,
				sel = false;

			for (var b = 0; b < sels.length; b++)
				if (vsplit(sels[b].vp)[1] == lin)
					sel = true;

			clmod(lis[a], 'hl', lin == fn);
			clmod(lis[a], 'sel', sel);
			if (lin == fn && sel)
				actsel = true;
		}
		clmod(ebi('seldoc'), 'sel', actsel);
	};

	r.tglsel = function () {
		var fn = ebi('docname').textContent;
		for (var a = 0; a < r.files.length; a++)
			if (r.files[a].name == fn)
				clmod(ebi(r.files[a].id).closest('tr'), 'sel', 't');

		msel.selui();
	};

	r.tgltail = function () {
		if (!window.TextDecoderStream) {
			bcfg_set('taildoc', r.taildoc = false);
			return toast.err(10, L.tail_2old);
		}
		r.show(r.url, true);
	};

	r.tglwrap = function () {
		r.show(r.url, true);
	};

	var bdoc = ebi('bdoc');
	bdoc.className = 'line-numbers';
	bdoc.innerHTML = (
		'<div id="hdoc" class="ghead">\n' +
		'<a href="#" class="btn" id="xdoc" tt="' + L.tvt_close + '</a>\n' +
		'<a href="#" class="btn" id="dldoc" tt="' + L.tvt_dl + '</a>\n' +
		'<a href="#" class="btn" id="prevdoc" tt="' + L.tvt_prev + '</a>\n' +
		'<a href="#" class="btn" id="nextdoc" tt="' + L.tvt_next + '</a>\n' +
		'<a href="#" class="btn" id="seldoc" tt="' + L.tvt_sel + '</a>\n' +
		'<a href="#" class="btn" id="editdoc" tt="' + L.tvt_edit + '</a>\n' +
		'<a href="#" class="btn tgl" id="taildoc" tt="' + L.tvt_tail + '</a>\n' +
		'<div id="tailbtns">\n' +
		'<a href="#" class="btn tgl" id="wrapdoc" tt="' + L.tvt_wrap + '</a>\n' +
		'<a href="#" class="btn tgl" id="tail2end" tt="' + L.tvt_atail + '</a>\n' +
		'<a href="#" class="btn tgl" id="tailansi" tt="' + L.tvt_ctail + '</a>\n' +
		'<input type="text" id="tailnb" value="" ' + NOAC + ' style="width:4em" tt="' + L.tvt_ntail + '" />' +
		'</div>\n' +
		'</div>'
	);
	ebi('xdoc').onclick = function () {
		r.untail();
		thegrid.setvis(true);
		bcfg_bind(r, 'taildoc', 'taildoc', false, r.tgltail);
	};
	ebi('dldoc').setAttribute('download', '');
	ebi('prevdoc').onclick = function () { tree_neigh(-1); };
	ebi('nextdoc').onclick = function () { tree_neigh(1); };
	ebi('seldoc').onclick = r.tglsel;
	bcfg_bind(r, 'wrap', 'wrapdoc', true, r.tglwrap);
	bcfg_bind(r, 'taildoc', 'taildoc', false, r.tgltail);
	bcfg_bind(r, 'tail2end', 'tail2end', true);
	bcfg_bind(r, 'tailansi', 'tailansi', false, r.tgltail);

	r.tailnb = ebi('tailnb').value = icfg_get('tailnb', 131072);
	ebi('tailnb').oninput = function (e) {
		swrite('tailnb', r.tailnb = this.value);
	};

	if (/[?&]tail\b/.exec(sloc0)) {
		clmod(ebi('taildoc'), 'on', 1);
		r.taildoc = true;
	}

	return r;
})();


var thegrid = (function () {
	var lfiles = ebi('files'),
		gfiles = mknod('div', 'gfiles');

	gfiles.style.display = 'none';
	gfiles.innerHTML = (
		'<div id="ghead" class="ghead">' +
		'<a href="#" class="tgl btn" id="gridvau" tt="' + L.gt_vau + '</a> ' +
		'<a href="#" class="tgl btn" id="gridsel" tt="' + L.gt_msel + '</a> ' +
		'<a href="#" class="tgl btn" id="gridcrop" tt="' + L.gt_crop + '</a> ' +
		'<a href="#" class="tgl btn" id="grid3x" tt="' + L.gt_3x + '</a> ' +
		'<span>' + L.gt_zoom + ': ' +
		'<a href="#" class="btn" z="-1.1" tt="Hotkey: shift-A">&ndash;</a> ' +
		'<a href="#" class="btn" z="1.1" tt="Hotkey: shift-D">+</a></span> <span>' + L.gt_chop + ': ' +
		'<a href="#" class="btn" l="-1" tt="' + L.gt_c1 + '">&ndash;</a> ' +
		'<a href="#" class="btn" l="1" tt="' + L.gt_c2 + '">+</a></span> <span>' + L.gt_sort + ': ' +
		'<a href="#" s="href">' + L.gt_name + '</a> ' +
		'<a href="#" s="sz">' + L.gt_sz + '</a> ' +
		'<a href="#" s="ts">' + L.gt_ts + '</a> ' +
		'<a href="#" s="ext">' + L.gt_ext + '</a>' +
		'</span></div>' +
		'<div id="ggrid"></div>'
	);
	lfiles.parentNode.insertBefore(gfiles, lfiles);
	var ggrid = ebi('ggrid');

	var r = {
		'sz': clamp(fcfg_get('gridsz', 10), 4, 80),
		'ln': clamp(icfg_get('gridln', 3), 1, 7),
		'isdirty': true,
		'bbox': null
	};

	var btnclick = function (e) {
		ev(e);
		var s = this.getAttribute('s'),
			z = this.getAttribute('z'),
			l = this.getAttribute('l');

		if (z)
			return setsz(z > 0 ? r.sz * z : r.sz / (-z));

		if (l)
			return setln(parseInt(l));

		var t = lfiles.tHead.rows[0].cells;
		for (var a = 0; a < t.length; a++)
			if (t[a].getAttribute('name') == s) {
				t[a].click();
				break;
			}

		r.setdirty();
	};

	var links = QSA('#ghead a');
	for (var a = 0; a < links.length; a++)
		links[a].onclick = btnclick;

	r.setvis = function (force) {
		if (showfile.active()) {
			if (!force)
				return;

			hist_push(get_evpath() + (dk ? '?k=' + dk : ''));
			wintitle();
		}

		lfiles = ebi('files');
		gfiles = ebi('gfiles');
		ggrid = ebi('ggrid');

		var vis = has(perms, "read");
		gfiles.style.display = vis && r.en ? '' : 'none';
		lfiles.style.display = vis && !r.en ? '' : 'none';
		clmod(ggrid, 'crop', r.crop);
		clmod(ggrid, 'nocrop', !r.crop);
		ebi('pro').style.display = ebi('epi').style.display = ebi('lazy').style.display = ebi('treeul').style.display = ebi('treepar').style.display = '';
		ebi('bdoc').style.display = 'none';
		clmod(ebi('wrap'), 'doc');
		qsr('#docname');
		if (treectl)
			treectl.textmode(false);

		if (filecols)
			filecols.uivis();

		aligngriditems();
		restore_scroll();
	};

	r.setdirty = function () {
		r.dirty = true;
		if (r.en)
			loadgrid();
		else
			r.setvis();
	};

	function setln(v) {
		if (v) {
			r.ln += v;
			if (r.ln < 1) r.ln = 1;
			if (r.ln > 7) r.ln = v < 0 ? 7 : 99;
			swrite('gridln', r.ln);
			setTimeout(r.tippen, 20);
		}
		setcvar('--grid-ln', r.ln);
	}
	setln();

	function setsz(v) {
		if (v !== undefined) {
			r.sz = clamp(v, 4, 80);
			swrite('gridsz', r.sz);
			setTimeout(r.tippen, 20);
		}
		setcvar('--grid-sz', r.sz + 'em');
		aligngriditems();
	}
	setsz();

	function gclick1(e) {
		if (ctrl(e) && !treectl.csel && !r.sel)
			return true;

		return gclick.call(this, e, false);
	}

	function gclick2(e) {
		if (ctrl(e) || !r.sel)
			return true;

		return gclick.call(this, e, true);
	}

	function gclick(e, dbl) {
		var oth = ebi(this.getAttribute('ref')),
			href = noq_href(this),
			fid = oth.getAttribute('id'),
			aplay = ebi('a' + fid),
			atext = ebi('t' + fid),
			is_txt = atext && !/\.ts$/.test(href) && showfile.getlang(href),
			is_img = img_re.test(href),
			is_dir = href.endsWith('/'),
			is_srch = !!ebi('unsearch'),
			in_tree = is_dir && treectl.find(oth.textContent.slice(0, -1)),
			have_sel = QS('#files tr.sel'),
			td = oth.closest('td').nextSibling,
			tr = td.parentNode;

		if (!is_srch && ((r.sel && !dbl && !ctrl(e)) || (treectl.csel && (e.shiftKey || ctrl(e))))) {
			td.onclick.call(td, e);
			if (e.shiftKey)
				return r.loadsel();
			clmod(this, 'sel', clgot(tr, 'sel'));
		}
		else if (in_tree && !have_sel)
			in_tree.click();

		else if (oth.hasAttribute('download'))
			oth.click();

		else if (aplay && (r.vau || !is_img))
			aplay.click();

		else if (is_dir && !have_sel)
			treectl.reqls(href, true);

		else if (is_txt && !has(['md', 'htm', 'html'], is_txt))
			atext.click();

		else if (!is_img && have_sel)
			window.open(href, '_blank');

		else {
			if (!dbl)
				return true;

			setTimeout(function () {
				r.sel = true;
			}, 1);
			r.sel = false;
			this.click();
		}
		ev(e);
	}

	r.imshow = function (url) {
		var sel = '#ggrid>a'
		if (!thegrid.en) {
			thegrid.bagit('#files');
			sel = '#files a[id]';
		}
		var ims = QSA(sel);
		for (var a = 0, aa = ims.length; a < aa; a++) {
			var iu = ims[a].getAttribute('href').split('?')[0].split('/').slice(-1)[0];
			if (iu == url)
				return ims[a].click();
		}
		baguetteBox.hide();
	};

	r.loadsel = function () {
		if (r.dirty)
			return;

		var ths = QSA('#ggrid>a');

		for (var a = 0, aa = ths.length; a < aa; a++) {
			var tr = ebi(ths[a].getAttribute('ref')).closest('tr'),
				cl = tr.className || '';

			if (noq_href(ths[a]).endsWith('/'))
				cl += ' dir';

			ths[a].className = cl;
		}

		var sp = ['unsearch', 'moar'];
		for (var a = 0; a < sp.length; a++)
			(function (a) {
				var o = QS('#ggrid a[ref="' + sp[a] + '"]');
				if (o)
					o.onclick = function (e) {
						ev(e);
						ebi(sp[a]).click();
					};
			})(a);
	};

	r.tippen = function () {
		var els = QSA('#ggrid>a>span'),
			aa = els.length;

		if (!aa)
			return;

		var cs = window.getComputedStyle(els[0]),
			fs = parseFloat(cs.lineHeight),
			pad = parseFloat(cs.paddingTop),
			pels = [],
			todo = [];

		for (var a = 0; a < aa; a++) {
			var vis = Math.round((els[a].offsetHeight - pad) / fs),
				all = Math.round((els[a].scrollHeight - pad) / fs),
				par = els[a].parentNode;

			pels.push(par);
			todo.push(vis < all ? par.getAttribute('ttt') : null);
		}

		for (var a = 0; a < todo.length; a++) {
			if (todo[a])
				pels[a].setAttribute('tt', todo[a]);
			else
				pels[a].removeAttribute('tt');
		}

		tt.att(ggrid);
	};

	function loadgrid() {
		if (have_webp === null)
			return setTimeout(loadgrid, 50);

		r.setvis();
		if (!r.dirty)
			return r.loadsel();

		if (dcrop.startsWith('f') || !sread('gridcrop'))
			bcfg_upd_ui('gridcrop', r.crop = ('y' == dcrop.slice(-1)));

		if (dth3x.startsWith('f') || !sread('grid3x'))
			bcfg_upd_ui('grid3x', r.x3 = ('y' == dth3x.slice(-1)));

		var html = [],
			svgs = new Set(),
			max_svgs = CHROME ? 500 : 5000,
			need_ext = !r.thumbs || !!ext_th,
			use_ext_th = r.thumbs && ext_th,
			files = QSA('#files>tbody>tr>td:nth-child(2) a[id]');

		for (var a = 0, aa = files.length; a < aa; a++) {
			var ao = files[a],
				ohref = esc(ao.getAttribute('href')),
				href = ohref.split('?')[0],
				ext = '',
				ext0 = '',
				name = uricom_dec(vsplit(href)[1]),
				ref = ao.getAttribute('id'),
				isdir = href.endsWith('/'),
				ac = isdir ? ' class="dir"' : '',
				ihref = ohref;

			if (need_ext && href != "#") {
				var ar = href.split('.');
				if (ar.length > 1)
					ar.shift();

				ar.reverse();
				ext0 = ar[0];
				for (var b = 0; b < Math.min(2, ar.length); b++) {
					if (ar[b].length > 7)
						break;

					ext = ext ? (ar[b] + '.' + ext) : ar[b];
				}
				if (!ext)
					ext = 'unk';
			}

			if (use_ext_th && (ext_th[ext] || ext_th[ext0])) {
				ihref = ext_th[ext] || ext_th[ext0];
			}
			else if (r.thumbs) {
				ihref = addq(ihref, 'th=' + (have_webp ? 'w' : 'j'));
				if (!r.crop)
					ihref += 'f';
				if (r.x3)
					ihref += '3';
				if (href == "#")
					ihref = SR + '/.cpr/ico/' + (ref == 'moar' ? '++' : 'exit');
			}
			else if (isdir) {
				ihref = SR + '/.cpr/ico/folder';
			}
			else {
				if (!svgs.has(ext)) {
					if (svgs.size < max_svgs)
						svgs.add(ext);
					else
						ext = "unk";
				}
				ihref = SR + '/.cpr/ico/' + ext;
			}
			ihref = addq(ihref, 'cache=i&_=' + ACB + TS);
			if (CHROME)
				ihref += "&raster";

			html.push('<a href="' + ohref + '" ref="' + ref +
				'"' + ac + ' ttt="' + esc(name) + '"><img style="height:' +
				(r.sz / 1.25) + 'em" loading="lazy" onload="th_onload(this)" src="' +
				ihref + '" /><span' + ac + '>' + ao.innerHTML + '</span></a>');
		}
		ggrid.innerHTML = html.join('\n');
		clmod(ggrid, 'crop', r.crop);
		clmod(ggrid, 'nocrop', !r.crop);

		var srch = ebi('unsearch'),
			gsel = ebi('gridsel');

		gsel.style.display = srch ? 'none' : '';
		if (srch && r.sel)
			gsel.click();

		var ths = QSA('#ggrid>a');
		for (var a = 0, aa = ths.length; a < aa; a++) {
			ths[a].ondblclick = gclick2;
			ths[a].onclick = gclick1;
		}

		r.dirty = false;
		r.bagit('#ggrid');
		r.loadsel();
		aligngriditems();
		setTimeout(r.tippen, 20);
	}

	r.bagit = function (isrc) {
		if (!window.baguetteBox)
			return;

		if (r.bbox)
			baguetteBox.destroy();

		var br = baguetteBox.run(isrc, {
			noScrollbars: true,
			duringHide: r.onhide,
			afterShow: function () {
				r.bbox_opts.refocus = true;
			},
			captions: function (g) {
				var idx = -1,
					h = '' + g;

				for (var a = 0; a < r.bbox.length; a++)
					if (r.bbox[a].imageElement == g)
						idx = a;

				return '<a download href="' + h +
					'">' + (idx + 1) + ' / ' + r.bbox.length + ' -- ' +
					esc(uricom_dec(h.split('/').pop())) + '</a>';
			},
			onChange: function (i) {
				sethash('g' + r.bbox[i].imageElement.getAttribute('ref') + getsort());
			}
		});
		r.bbox = br[0][0];
		r.bbox_opts = br[1];
	};

	r.onhide = function () {
		afilt.apply();

		if (!thegrid.ihop)
			return;

		try {
			var el = QS('#ggrid a[ref="' + location.hash.slice(2) + '"]'),
				f = function () {
					try {
						el.focus();
					}
					catch (ex) { }
				};

			f();
			setTimeout(f, 10);
			setTimeout(f, 100);
			setTimeout(f, 200);
			// thx fullscreen api

			if (ANIM) {
				clmod(el, 'glow', 1);
				setTimeout(function () {
					try {
						clmod(el, 'glow');
					}
					catch (ex) { }
				}, 600);
			}
			r.bbox_opts.refocus = false;
		}
		catch (ex) {
			console.log('ihop:', ex);
		}
	};

	r.set_crop = function (en) {
		if (!dcrop.startsWith('f'))
			return r.setdirty();

		r.crop = dcrop.endsWith('y');
		bcfg_upd_ui('gridcrop', r.crop);
		if (r.crop != en)
			toast.warn(10, L.ul_btnlk);
	};

	r.set_x3 = function (en) {
		if (!dth3x.startsWith('f'))
			return r.setdirty();

		r.x3 = dth3x.endsWith('y');
		bcfg_upd_ui('grid3x', r.x3);
		if (r.x3 != en)
			toast.warn(10, L.ul_btnlk);
	};

	if (/[?&]grid\b/.exec(sloc0))
		swrite('griden', /[?&]grid=0\b/.exec(sloc0) ? 0 : 1)

	if (/[?&]thumb\b/.exec(sloc0))
		swrite('thumbs', /[?&]thumb=0\b/.exec(sloc0) ? 0 : 1)

	if (/[?&]imgs\b/.exec(sloc0)) {
		var n = /[?&]imgs=0\b/.exec(sloc0) ? 0 : 1;
		swrite('griden', n);
		if (n)
			swrite('thumbs', 1);
	}

	bcfg_bind(r, 'thumbs', 'thumbs', true, r.setdirty);
	bcfg_bind(r, 'ihop', 'ihop', true);
	bcfg_bind(r, 'vau', 'gridvau', false);
	bcfg_bind(r, 'crop', 'gridcrop', !dcrop.endsWith('n'), r.set_crop);
	bcfg_bind(r, 'x3', 'grid3x', dth3x.endsWith('y'), r.set_x3);
	bcfg_bind(r, 'sel', 'gridsel', false, r.loadsel);
	bcfg_bind(r, 'en', 'griden', dgrid, function (v) {
		v ? loadgrid() : r.setvis(true);
		pbar.onresize();
		vbar.onresize();
	});
	ebi('wtgrid').onclick = ebi('griden').onclick;

	return r;
})();


function th_onload(el) {
	el.style.height = '';
}


function tree_scrollto(e) {
	ev(e);
	tree_scrolltoo('#treeul a.hl');
	tree_scrolltoo('#docul a.hl');
}


function tree_scrolltoo(q) {
	var act = QS(q),
		ul = act ? act.offsetParent : null;

	if (!ul)
		return;

	var ctr = ebi('tree'),
		em = parseFloat(getComputedStyle(act).fontSize),
		top = act.offsetTop + ul.offsetTop,
		min = top - 20 * em,
		max = top - (ctr.offsetHeight - 16 * em);

	if (ctr.scrollTop > min)
		ctr.scrollTop = Math.floor(min);
	else if (ctr.scrollTop < max)
		ctr.scrollTop = Math.floor(max);
}


function tree_neigh(n, ratelimit) {
	if (ratelimit && QS('.dumb_loader_thing') && Date.now() - treectl.busied < 5)
		return;

	var links = QSA(showfile.active() || treectl.texts ? '#docul li>a' : '#treeul li>a+a');
	if (!links.length) {
		treectl.dir_cb = function () {
			tree_neigh(n);
			treectl.detree();
		};
		treectl.entree(null, true);
		return;
	}
	var act = -1;
	for (var a = 0, aa = links.length; a < aa; a++) {
		if (clgot(links[a], 'hl')) {
			act = a;
			break;
		}
	}
	if (act == -1 && !treectl.texts)
		return;

	act += n;
	if (act < 0)
		act = links.length - 1;
	if (act >= links.length)
		act = 0;

	if (showfile.active())
		links[act].click();
	else
		treectl.treego.call(links[act]);
}


function tree_up(justgo) {
	if (showfile.active())
		return thegrid.setvis(true);

	var act = QS('#treeul a.hl');
	if (!act) {
		treectl.dir_cb = function () {
			tree_up(justgo);
			treectl.detree();
		};
		treectl.entree(null, true);
		return;
	}
	if (act.previousSibling.textContent == '-') {
		act.previousSibling.click();
		if (!justgo)
			return;
	}
	var a = act.parentNode.parentNode.parentNode.getElementsByTagName('a')[1];
	if (a.parentNode.tagName == 'LI')
		a.click();
}


function hkhelp() {
	var html = [];
	for (var ic = 0; ic < L.hks.length; ic++) {
		var c = L.hks[ic];
		html.push('<table>');
		for (var a = 0; a < c.length; a++)
			try {
				if (c[a].length != 2)
					html.push('<tr><th colspan="2">' + esc(c[a]) + '</th></tr>');
				else {
					var t1 = c[a][0].replace('⇧', '<b>⇧</b>');
					html.push('<tr><td>{0}</td><td>{1}</td></tr>'.format(t1, c[a][1]));
				}
			}
			catch (ex) {
				html.push(">>> " + c[a]);
			}

		html.push('</table>');
	}
	qsr('#hkhelp');
	var o = mknod('div', 'hkhelp');
	o.innerHTML = html.join('\n');
	document.body.appendChild(o);
}


var fselgen, fselctr;
function fselfunw(e, ae, d, rem) {
	fselctr = 0;
	var gen = fselgen = Date.now();
	if (rem)
		rem *= window.innerHeight;

	var selfun = function () {
		var el = ae[d + 'ElementSibling'];
		if (!el || gen != fselgen)
			return;

		el.focus();
		var elh = el.offsetHeight;
		if (ctrl(e))
			document.documentElement.scrollTop += (d == 'next' ? 1 : -1) * elh;

		if (e.shiftKey) {
			clmod(el, 'sel', 't');
			msel.origin_tr(el);
			msel.selui();
		}

		rem -= elh;
		if (rem > 0) {
			ae = document.activeElement;
			if (++fselctr % 5 && rem > elh * (FIREFOX ? 5 : 2))
				selfun();
			else
				setTimeout(selfun, 1);
		}
	}
	selfun();
}
var konmai = 0, konmak = (function() {
	var u = "arrowup",
		d = "arrowdown",
		l = "arrowleft",
		r = "arrowright";
	return [u, u, d, d, l, r, l, r, "b", "a", "enter"];
})();
var ahotkeys = function (e) {
	if (e.altKey || e.isComposing)
		return;

	if (QS('#bbox-overlay.visible') || modal.busy)
		return;

	var k = (e.key || e.code) + '', pos = -1, n,
		ae = document.activeElement,
		aet = ae && ae != document.body ? ae.nodeName.toLowerCase() : '';

	if (k.startsWith('Key'))
		k = k.slice(3);
	else if (k.startsWith('Digit'))
		k = k.slice(5);

	var kl = k.toLowerCase();

	if (dbg_kbd)
		console.log('KBD', k, kl, e.key, e.code, e.keyCode, e.which);

	if (konmai < 0)
		noop();
	else if (konmak[konmai] != kl)
		konmai = konmai && kl == konmak[0] ? (konmai<3?konmai:1):0;
	else if (++konmai >= konmak.length) {
		konmai = -1;
		document.documentElement.scrollTop = 0;
		settheme.go(6);
		start_actx();
		sfx_nice();
		toast.inf(9, 'omega clearance granted', null, 'top');
		setTimeout(function() {
			apply_perms(treectl.lsc);
			fileman.render();
		}, 573);
		return ev(e);
	}

	if (k == 'Escape' || k == 'Esc') {
		ae && ae.blur();
		tt.hide();

		if (ebi('hkhelp'))
			return qsr('#hkhelp');

		if (toast.visible)
			return toast.hide();

		if (ebi('rn_cancel'))
			return ebi('rn_cancel').click();

		if (ebi('sh_abrt'))
			return ebi('sh_abrt').click();

		if (QS('.opview.act'))
			return QS('#ops>a').click();

		if (widget.is_open)
			return widget.close();

		if (showfile.active())
			return thegrid.setvis(true);

		if (!treectl.hidden)
			return treectl.detree();

		if (QS('#unsearch'))
			return QS('#unsearch').click();

		if (thegrid.en)
			return ebi('griden').click();
	}

	var in_ftab = (aet == 'tr' || aet == 'td') && ae.closest('#files');
	if (in_ftab) {
		var d = '', rem = 0;
		if (aet == 'td') ae = ae.closest('tr'); //ie11
		if (k == 'ArrowUp' || k == 'Up') d = 'previous';
		if (k == 'ArrowDown' || k == 'Down') d = 'next';
		if (k == 'PageUp') { d = 'previous'; rem = 0.6; }
		if (k == 'PageDown') { d = 'next'; rem = 0.6; }
		if (d) {
			fselfunw(e, ae, d, rem);
			return ev(e);
		}
		if (k == 'Space' || k == 'Spacebar' || k == ' ') {
			clmod(ae, 'sel', 't');
			msel.origin_tr(ae);
			msel.selui();
			return ev(e);
		}
	}
	if (in_ftab || !aet || (ae && ae.closest('#ggrid'))) {
		if ((kl == 'a') && ctrl(e)) {
			var ntot = treectl.lsc.files.length + treectl.lsc.dirs.length,
				sel = msel.getsel(),
				all = msel.getall();

			msel.evsel(e, sel.length < all.length);
			msel.origin_id(null);
			if (ntot > all.length)
				toast.warn(10, L.f_anota.format(all.length, ntot), L.f_anota);
			else if (toast.tag == L.f_anota)
				toast.hide();
			return ev(e);
		}
	}

	if (ae && ae.closest('pre')) {
		if ((kl == 'a') && ctrl(e)) {
			var sel = document.getSelection(),
				ran = document.createRange();

			sel.removeAllRanges();
			ran.selectNode(ae.closest('pre'));
			sel.addRange(ran);
			return ev(e);
		}
	}

	if (k.endsWith('Enter') && ae && (ae.onclick || ae.hasAttribute('tabIndex')))
		return ev(e) && ae.click() || true;

	if (aet && aet != 'a' && aet != 'tr' && aet != 'td' && aet != 'div' && aet != 'pre')
		return;

	if (k == '?')
		return hkhelp();

	if (!e.shiftKey && ctrl(e)) {
		var sel = window.getSelection && window.getSelection() || {};
		sel = sel && !sel.isCollapsed && sel.direction != 'none';

		if (kl == 'x')
			return fileman.cut(e);

		if (kl == 'c' && !sel)
			return fileman.cpy(e);

		if (kl == 'v')
			return fileman.d_paste(e);

		if (kl == 'k')
			return fileman.delete(e);

		return;
	}

	if (e.shiftKey && kl != 'a' && kl != 'd')
		return;

	if (/^[0-9]$/.test(k))
		pos = parseInt(k) * 0.1;

	if (pos !== -1)
		return seek_au_mul(pos) || true;

	if (kl == 'j')
		return prev_song() || true;

	if (kl == 'l')
		return next_song() || true;

	if (kl == 'p')
		return playpause() || true;

	n = kl == 'u' ? -10 : kl == 'o' ? 10 : 0;
	if (n !== 0)
		return seek_au_rel(n) || true;

	if (kl == 'y')
		return msel.getsel().length ? ebi('seldl').click() :
			showfile.active() ? ebi('dldoc').click() :
				dl_song();

	n = kl == 'i' ? -1 : kl == 'k' ? 1 : 0;
	if (n !== 0)
		return tree_neigh(n, 1);

	if (kl == 'm')
		return tree_up();

	if (kl == 'b')
		return treectl.hidden ? treectl.entree() : treectl.detree();

	if (kl == 'g')
		return ebi('griden').click();

	if (kl == 't')
		return ebi('thumbs').click();

	if (kl == 'v')
		return ebi('filetree').click();

	if (k == 'F2')
		return fileman.rename();

	if (!treectl.hidden && (!e.shiftKey || !thegrid.en)) {
		if (kl == 'a')
			return QS('#twig').click();

		if (kl == 'd')
			return QS('#twobytwo').click();
	}

	if (showfile.active()) {
		if (kl == 's')
			showfile.tglsel();
		if (kl == 'e' && ebi('editdoc').style.display != 'none')
			ebi('editdoc').click();
	}

	if (mp && mp.au && !mp.au.paused) {
		if (kl == 's')
			return sel_song();
	}

	if (thegrid.en) {
		if (kl == 's')
			return ebi('gridsel').click();

		if (kl == 'a')
			return QSA('#ghead a[z]')[0].click();

		if (kl == 'd')
			return QSA('#ghead a[z]')[1].click();
	}
};


// search
var search_ui = (function () {
	var sconf = [
		[
			L.s_sz,
			["szl", "sz_min", L.s_s1, "14", ""],
			["szu", "sz_max", L.s_s2, "14", ""]
		],
		[
			L.s_dt,
			["dtl", "dt_min", L.s_d1, "14", "1997-08-15, 01:00"],
			["dtu", "dt_max", L.s_d2, "14", "2020"]
		],
		[
			L.s_rd,
			["path", "path", L.s_r1, "30", "windows  -system32"]
		],
		[
			L.s_fn,
			["name", "name", L.s_f1, "30", ".exe$"]
		],
		[
			L.s_ta,
			["tags", "tags", L.s_t1, "30", "^irui$"]
		],
		[
			L.s_ad,
			["adv", "adv", L.s_a1, "30", "key>=1A  key<=2B  .bpm>165"]
		],
		[
			L.s_ua,
			["utl", "ut_min", L.s_u1, "14", "2007-04-08"],
			["utu", "ut_max", L.s_u2, "14", "2038-01-19"]
		]
	];

	var r = {},
		trs = [],
		orig_url = null,
		orig_html = null,
		cap = 125;

	for (var a = 0; a < sconf.length; a++) {
		var html = ['<tr id="tsrch_' + sconf[a][1][0] + '"><td><br />' + sconf[a][0] + '</td>'];
		for (var b = 1; b < 3; b++) {
			var hn = "srch_" + sconf[a][b][0],
				csp = (sconf[a].length == 2) ? 2 : 1;

			html.push(
				'<td colspan="' + csp + '"><input id="' + hn + 'c" type="checkbox">\n' +
				'<label for="' + hn + 'c">' + sconf[a][b][2] + '</label>\n' +
				'<br /><input id="' + hn + 'v" type="text" style="width:' + sconf[a][b][3] +
				'em" name="' + sconf[a][b][1] + '" placeholder="' + sconf[a][b][4] + '" /></td>');
			if (csp == 2)
				break;
		}
		html.push('</tr>');
		trs.push(html);
	}
	var html = [];
	for (var a = 0; a < trs.length; a += 2) {
		html.push('<table>' + (trs[a].concat(trs[a + 1])).join('\n') + '</table>');
	}
	html.push('<table id="tq_raw"><tr><td>raw</td><td><input id="q_raw" type="text" name="q" ' + NOAC + ' placeholder="( tags like *nhato* or tags like *taishi* ) and ( not tags like *nhato* or not tags like *taishi* )" /></td></tr></table>');
	ebi('srch_form').innerHTML = html.join('\n');

	var o = QSA('#op_search input');
	for (var a = 0; a < o.length; a++) {
		o[a].oninput = ev_search_input;
		o[a].onkeydown = ev_search_keydown;
	}

	function srch_msg(err, txt) {
		var o = ebi('srch_q');
		o.textContent = txt;
		clmod(o, 'err', err);
	}

	var search_timeout,
		defer_timeout,
		search_in_progress = 0;

	function ev_search_input() {
		var v = unsmart(this.value),
			id = this.getAttribute('id'),
			is_txt = id.slice(-1) == 'v',
			is_chk = id.slice(-1) == 'c';

		if (is_txt) {
			var chk = ebi(id.slice(0, -1) + 'c');
			chk.checked = ((v + '').length > 0);
		}

		if (id != "q_raw")
			encode_query();

		set_vq();
		cap = 125;

		clearTimeout(defer_timeout);
		if (is_chk)
			return do_search();

		defer_timeout = setTimeout(try_search, 2000);
		try_search(v);
	}

	function ev_search_keydown(e) {
		if ((e.key + '').endsWith('Enter'))
			do_search();
	}

	function try_search(v) {
		if (Date.now() - search_in_progress > 30 * 1000) {
			clearTimeout(defer_timeout);
			clearTimeout(search_timeout);
			search_timeout = setTimeout(do_search,
				v && v.length < (MOBILE ? 4 : 3) ? 1000 : 500);
		}
	}

	function set_vq() {
		if (search_in_progress)
			return;

		var q = unsmart(ebi('q_raw').value),
			vq = ebi('files').getAttribute('q_raw');

		srch_msg(false, (q == vq) ? '' : L.sm_prev + (vq ? vq : '(*)'));
	}

	function encode_query() {
		var q = '';
		for (var a = 0; a < sconf.length; a++) {
			for (var b = 1; b < sconf[a].length; b++) {
				var k = sconf[a][b][0],
					chk = 'srch_' + k + 'c',
					vs = unsmart(ebi('srch_' + k + 'v').value),
					tvs = [];

				if (a == 1)
					vs = vs.trim().replace(/ +/, 'T');

				while (vs) {
					vs = vs.trim();
					if (!vs)
						break;

					var v = '';
					if (vs.startsWith('"')) {
						var vp = vs.slice(1).split(/"(.*)/);
						v = vp[0];
						vs = vp[1] || '';
						while (v.endsWith('\\')) {
							vp = vs.split(/"(.*)/);
							v = v.slice(0, -1) + '"' + vp[0];
							vs = vp[1] || '';
						}
					}
					else {
						var vp = vs.split(/ +(.*)/);
						v = vp[0].replace(/\\"/g, '"');
						vs = vp[1] || '';
					}
					tvs.push(v);
				}

				if (!ebi(chk).checked)
					continue;

				for (var c = 0; c < tvs.length; c++) {
					var tv = tvs[c];
					if (!tv.length)
						break;

					q += ' and ';

					if (k == 'adv') {
						q += tv.replace(/ +/g, " and ").replace(/([=!><]=?)/, " $1 ");
						continue;
					}

					if (k.length == 3) {
						q += k.replace(/l$/, ' >= ').replace(/u$/, ' <= ').replace(/^sz/, 'size').replace(/^dt/, 'date').replace(/^ut/, 'up_at') + tv;
						continue;
					}

					if (k == 'path' || k == 'name' || k == 'tags') {
						var not = '';
						if (tv.slice(0, 1) == '-') {
							tv = tv.slice(1);
							not = 'not ';
						}

						if (tv.slice(0, 1) == '^') {
							tv = tv.slice(1);
						}
						else {
							tv = '*' + tv;
						}

						if (tv.slice(-1) == '$') {
							tv = tv.slice(0, -1);
						}
						else {
							tv += '*';
						}

						if (tv.indexOf(' ') + 1) {
							tv = '"' + tv + '"';
						}

						q += not + k + ' like ' + tv;
					}
				}
			}
		}
		ebi('q_raw').value = q.slice(5);
	}

	function do_search() {
		search_in_progress = Date.now();
		srch_msg(false, L.sm_w8);
		clearTimeout(search_timeout);

		var xhr = new XHR();
		xhr.open('POST', SR + '/?srch', true);
		xhr.setRequestHeader('Content-Type', 'text/plain');
		xhr.onload = xhr.onerror = xhr_search_results;
		xhr.ts = Date.now();
		xhr.q_raw = unsmart(ebi('q_raw').value);
		xhr.send(JSON.stringify({ "q": xhr.q_raw, "n": cap }));
	}

	function xhr_search_results() {
		if (this.status !== 200) {
			var msg = hunpre(this.responseText);
			srch_msg(true, "http " + this.status + ": " + msg);
			search_in_progress = 0;
			return;
		}
		search_in_progress = 0;
		srch_msg(false, '');

		var res = JSON.parse(this.responseText);
		r.render(res, this, true);
	}

	r.render = function (res, xhr, sort) {
		var tagord = res.tag_order;

		srch_msg(false, '');
		if (sort)
			sortfiles(res.hits);

		var ofiles = ebi('files');
		if (xhr && ofiles.getAttribute('ts') > xhr.ts)
			return;

		treectl.hide();
		thegrid.setvis(true);

		var html = mk_files_header(tagord), seen = {};
		html.push('<tbody>');
		html.push('<tr class="srch_hdr"><td>-</td><td><a href="#" id="unsearch"><big style="font-weight:bold">[❌] ' + L.sl_close + '</big></a> -- ' + L.sl_hits.format(res.hits.length) + (res.trunc ? ' -- <a href="#" id="moar">' + L.sl_moar + '</a>' : '') + '</td></tr>');

		for (var a = 0; a < res.hits.length; a++) {
			var r = res.hits[a],
				ts = parseInt(r.ts),
				sz = parseInt(r.sz),
				hsz = filesizefun(sz),
				rp = esc(uricom_dec(r.rp + '')),
				ext = rp.lastIndexOf('.') > 0 ? rp.split('.').pop().split('?')[0] : '%',
				id = 'f-' + ('00000000' + crc32(rp)).slice(-8);

			while (seen[id])
				id += 'a';
			seen[id] = 1;

			if (ext.length > 8)
				ext = '%';

			var links = linksplit(r.rp + '', id).join('<span>/</span>'),
				nodes = ['<tr><td>-</td><td><div>' + links +
					'</div></td><td sortv="' + sz + '">' + hsz];

			for (var b = 0; b < tagord.length; b++) {
				var k = esc(tagord[b]),
					v = r.tags[k] || "";

				if (k == ".dur") {
					var sv = v ? s2ms(v) : "";
					nodes[nodes.length - 1] += '</td><td sortv="' + v + '">' + sv;
					continue;
				}

				nodes.push(esc('' + v));
			}

			nodes = nodes.concat([ext, unix2ui(ts)]);
			html.push(nodes.join('</td><td>'));
			html.push('</td></tr>');
		}

		if (!orig_html || orig_url != get_evpath()) {
			orig_html = ebi('files').innerHTML;
			orig_url = get_evpath();
		}

		ofiles = set_files_html(html.join('\n'));
		ofiles.setAttribute("ts", xhr ? xhr.ts : 1);
		ofiles.setAttribute("q_raw", xhr ? xhr.q_raw : 'playlist');
		set_vq();
		mukey.render();
		reload_browser();
		filecols.set_style(['File Name']);

		if (xhr)
			sethash('q=' + uricom_enc(xhr.q_raw));

		ebi('unsearch').onclick = unsearch;
		var m = ebi('moar');
		if (m)
			m.onclick = moar;
	};

	function unsearch(e) {
		ev(e);
		treectl.show();
		set_files_html(orig_html);
		ebi('files').removeAttribute('q_raw');
		orig_html = null;
		sethash('');
		reload_browser();
	}

	function moar(e) {
		ev(e);
		cap *= 2;
		do_search();
	}

	return r;
})();


function ev_load_m3u(e) {
	ev(e);
	var id = this.getAttribute('id').slice(1),
		url = ebi(id).getAttribute('href').split('?')[0];

	modal.confirm(L.mm_m3u,
		function () { load_m3u(url); },
		function () {
			if (has(perms, 'write') && has(perms, 'delete'))
				location = url + '?edit';
			else
				showfile.show(url);
		}
	);
	return false;
}
function load_m3u(url) {
	assert_vp(url);
	var xhr = new XHR();
	xhr.open('GET', url, true);
	xhr.onload = render_m3u;
	xhr.url = url;
	xhr.send();
	return false;
}
function render_m3u() {
	if (!xhrchk(this, L.tv_xe1, L.tv_xe2))
		return;

	var evp = get_evpath(),
		m3u = this.responseText,
		xtd = m3u.slice(0, 12).indexOf('#EXTM3U') + 1,
		lines = m3u.replace(/\r/g, '\n').split('\n'),
		dur = 1,
		artist = '',
		title = '',
		ret = {'hits': [], 'tag_order': ['artist', 'title', '.dur'], 'trunc': false};

	for (var a = 0; a < lines.length; a++) {
		var ln = lines[a].trim();
		if (xtd && ln.startsWith('#')) {
			var m = /^#EXTINF:([0-9]+)[, ](.*)/.exec(ln);
			if (m) {
				dur = m[1];
				title = m[2];
				var ofs = title.indexOf(' - ');
				if (ofs > 0) {
					artist = title.slice(0, ofs);
					title = title.slice(ofs + 3);
				}
			}
			continue;
		}
		if (ln.indexOf('.') < 0)
			continue;

		var n = ret.hits.length + 1,
			url = ln;

		if (url.indexOf(':\\'))  // C:\
			url = url.split(/\\/g).pop();

		url = url.replace(/\\/g, '/');
		url = uricom_enc(url).replace(/%2f/gi, '/')

		if (!url.startsWith('/'))
			url = vjoin(evp, url);

		ret.hits.push({
			"ts": 946684800 + n,
			"sz": 100000 + n,
			"rp": url,
			"tags": {".dur": dur, "artist": artist, "title": title}
		});
		dur = 1;
		artist = title = '';
	}

	search_ui.render(ret, null, false);
	sethash('m3u=' + this.url.split('?')[0].split('/').pop());
	goto();

	var el = QS('#files>tbody>tr.au>td>a.play');
	if (el)
		el.click();
}


function aligngriditems() {
	if (!treectl)
		return;

	var ggrid = ebi('ggrid'),
		em2px = parseFloat(getComputedStyle(ggrid).fontSize),
		gridsz = 10;
	try {
		gridsz = cprop('--grid-sz').slice(0, -2);
	}
	catch (ex) { }
	var gridwidth = ggrid.clientWidth,
		griditemcount = ggrid.children.length,
		totalgapwidth = em2px * griditemcount;

	if (/b/.test(themen + ''))
		totalgapwidth *= 2.8;

	var val, st = ggrid.style;

	if (((griditemcount * em2px) * gridsz) + totalgapwidth < gridwidth) {
		val = 'left';
	} else {
		val = treectl.hidden ? 'center' : 'space-between';
	}
	if (st.justifyContent != val)
		st.justifyContent = val;
}
onresize100.add(aligngriditems);


var filecolwidth = (function () {
	var lastwidth = -1;

	return function () {
		var vw = window.innerWidth / parseFloat(getComputedStyle(document.body)['font-size']),
			w = Math.floor(vw - 2);

		if (w == lastwidth)
			return;

		lastwidth = w;
		setcvar('--file-td-w', w + 'em');
	}
})();
onresize100.add(filecolwidth, true);


var treectl = (function () {
	var r = {
		"hidden": true,
		"sb_msg": false,
		"ls_cb": null,
		"dir_cb": tree_scrollto,
		"pdir": []
	},
		entreed = false,
		fixedpos = false,
		prev_atop = null,
		prev_winh = null,
		mentered = null,
		treesz = clamp(icfg_get('treesz', 16), 10, 50);

	var resort = function () {
		ENATSORT = NATSORT && clgot(ebi('nsort'), 'on');
		treectl.gentab(get_evpath(), treectl.lsc);
	};
	bcfg_bind(r, 'ireadme', 'ireadme', true);
	bcfg_bind(r, 'idxh', 'idxh', idxh, setidxh);
	bcfg_bind(r, 'dyn', 'dyntree', true, onresize);
	bcfg_bind(r, 'csel', 'csel', dgsel);
	bcfg_bind(r, 'dots', 'dotfiles', see_dots, function (v) {
		r.goto();
		var xhr = new XHR();
		xhr.open('GET', SR + '/?setck=dots=' + (v ? 'y' : ''), true);
		xhr.send();
	});
	bcfg_bind(r, 'utctid', 'utctid', dutc, function (v) {
		window.unix2ui = v ? unix2iso : unix2iso_localtime;
		resort();
	});
	bcfg_bind(r, 'nsort', 'nsort', dnsort, resort);
	bcfg_bind(r, 'dir1st', 'dir1st', true, resort);
	setwrap(bcfg_bind(r, 'wtree', 'wraptree', true, setwrap));
	setwrap(bcfg_bind(r, 'parpane', 'parpane', true, onscroll));
	bcfg_bind(r, 'htree', 'hovertree', false, reload_tree);
	bcfg_bind(r, 'ask', 'bd_ask', MOBILE && FIREFOX);
	ebi('bd_lim').value = r.lim = icfg_get('bd_lim');
	ebi('bd_lim').oninput = function (e) {
		var n = parseInt(this.value);
		swrite('bd_lim', r.lim = (isNum(n) ? n : 0) || 1000);
	};
	r.nvis = r.lim;

	ldks = jread('dks', []);
	for (var a = ldks.length - 1; a >= 0; a--) {
		var s = ldks[a],
			o = s.lastIndexOf('?');

		dks[s.slice(0, o)] = s.slice(o + 1);
	}

	function setwrap(v) {
		clmod(ebi('tree'), 'nowrap', !v);
		reload_tree();
	}
	setwrap(r.wtree);

	function setidxh(v) {
		if (!v == !/\bidxh=y\b/.exec('' + document.cookie))
			return;

		var xhr = new XHR();
		xhr.open('GET', SR + '/?setck=idxh=' + (v ? 'y' : 'n'), true);
		xhr.send();
	}
	setidxh(r.idxh);

	r.entree = function (e, nostore) {
		ev(e);
		entreed = true;
		if (!nostore)
			swrite('entreed', 'tree');

		get_tree("", get_evpath(), true);
		r.show();
	}

	r.show = function () {
		r.hidden = false;
		if (!entreed) {
			ebi('path').style.display = 'inline-block';
			return;
		}

		ebi('path').style.display = 'none';
		ebi('tree').style.display = 'block';
		window.addEventListener('scroll', onscroll);
		window.addEventListener('resize', onresize);
		onresize();
		aligngriditems();
	};

	r.detree = function (e) {
		ev(e);
		entreed = false;
		swrite('entreed', 'na');

		r.hide();
		ebi('path').style.display = '';
	}

	r.hide = function () {
		r.hidden = true;
		ebi('path').style.display = 'none';
		ebi('tree').style.display = 'none';
		ebi('wrap').style.marginLeft = '';
		window.removeEventListener('resize', onresize);
		window.removeEventListener('scroll', onscroll);
		aligngriditems();
	}

	function unmenter() {
		if (mentered) {
			mentered.style.position = '';
			mentered = null;
		}
	}

	r.textmode = function (ya) {
		var chg = !r.texts != !ya;
		r.texts = ya;
		ebi('docul').style.display = ya ? '' : 'none';
		ebi('treeul').style.display = ebi('treepar').style.display = ya ? 'none' : '';
		clmod(ebi('filetree'), 'on', ya);
		if (chg)
			tree_scrollto();
	};
	ebi('filetree').onclick = function (e) {
		ev(e);
		r.textmode(!r.texts);
	};
	r.textmode(false);

	function onscroll() {
		unmenter();
		onscroll2();
	}

	function onscroll2() {
		if (!entreed || r.hidden || document.visibilityState == 'hidden')
			return;

		var tree = ebi('tree'),
			wrap = ebi('wrap'),
			wraptop = null,
			atop = wrap.getBoundingClientRect().top,
			winh = window.innerHeight,
			parp = ebi('treepar'),
			y = tree.scrollTop,
			w = tree.offsetWidth;

		if (atop !== prev_atop || winh !== prev_winh)
			wraptop = Math.floor(wrap.offsetTop);

		if (r.parpane && r.pdir.length && w != r.pdirw) {
			r.pdirw = w;
			compy();
		}

		if (!r.parpane || !r.pdir.length || y >= r.pdir.slice(-1)[0][0] || y <= r.pdir[0][0]) {
			clmod(parp, 'off', 1);
			r.pdirh = null;
		}
		else {
			var h1 = [], h2 = [], els = [];
			for (var a = 0; a < r.pdir.length; a++) {
				if (r.pdir[a][0] > y)
					break;

				var e2 = r.pdir[a][1], e1 = e2.previousSibling;
				h1.push('<li>' + e1.outerHTML + e2.outerHTML + '<ul>');
				h2.push('</ul></li>');
				els.push([e1, e2]);
			}
			h1 = h1.join('\n') + h2.join('\n');
			if (h1 != r.pdirh) {
				r.pdirh = h1;
				parp.innerHTML = h1;
				clmod(parp, 'off');
				var els = QSA('#treepar a');
				for (var a = 0, aa = els.length; a < aa; a++)
					els[a].onclick = bad_proxy;
			}
			y = ebi('treeh').offsetHeight;
			if (!fixedpos)
				y += tree.offsetTop - yscroll();

			y = (y - 3) + 'px';
			if (parp.style.top != y)
				parp.style.top = y;
		}

		if (wraptop === null)
			return;

		prev_atop = atop;
		prev_winh = winh;

		if (fixedpos && atop >= 0) {
			tree.style.position = 'absolute';
			tree.style.bottom = '';
			fixedpos = false;
		}
		else if (!fixedpos && atop < 0) {
			tree.style.position = 'fixed';
			tree.style.height = 'auto';
			fixedpos = true;
		}

		if (fixedpos) {
			tree.style.top = Math.max(0, parseInt(atop)) + 'px';
		}
		else {
			var top = Math.max(0, wraptop),
				treeh = winh - atop;

			tree.style.top = top + 'px';
			tree.style.height = treeh < 10 ? '' : Math.floor(treeh) + 'px';
		}
	}
	timer.add(onscroll2, true);

	function onresize(e) {
		if (!entreed || r.hidden)
			return;

		var q = '#tree',
			nq = -3;

		while (r.dyn) {
			nq++;
			q += '>ul>li';
			if (!QS(q))
				break;
		}
		nq = Math.max(nq, get_evpath().split('/').length - 2);
		var iw = (treesz + Math.max(0, nq)),
			w = iw + 'em',
			w2 = (iw + 2) + 'em';

		setcvar('--nav-sz', w);
		ebi('tree').style.width = w;
		ebi('wrap').style.marginLeft = w2;
		onscroll();
	}

	r.find = function (txt) {
		var ta = QSA('#treeul a.hl+ul>li>a+a');
		for (var a = 0, aa = ta.length; a < aa; a++)
			if (ta[a].textContent == txt)
				return ta[a];
	};

	r.goto = function (url, push, back) {
		if (!url || !url.startsWith('/'))
			url = get_evpath() + (url || '');

		get_tree("", url, true);
		r.reqls(url, push, back);
	};

	function get_tree(top, dst, rst) {
		var xhr = new XHR(),
			m = /[?&](k=[^&#]+)/.exec(dst),
			k = m ? '&' + m[1] : dk ? '&k=' + dk : '';

		xhr.top = top;
		xhr.dst = dst;
		xhr.rst = rst;
		xhr.ts = r.busied = Date.now();
		xhr.open('GET', addq(dst, 'tree=' + top + (r.dots ? '&dots' : '') + k), true);
		xhr.onload = xhr.onerror = r.recvtree;
		xhr.send();
		enspin('t');
	}

	r.recvtree = function () {
		if (!xhrchk(this, L.tl_xe1, L.tl_xe2))
			return;

		try {
			var res = JSON.parse(this.responseText);
		}
		catch (ex) {
			return toast.err(30, "bad <code>?tree</code> reply;\nexpected json, got this:\n\n" + esc(this.responseText + ''));
		}
		r.rendertree(res, this.ts, this.top, this.dst, this.rst);

		if (r.lsc && r.lsc.unlist)
			r.prunetree(r.lsc);
	};

	r.prunetree = function (res) {
		var ptn = new RegExp(res.unlist);
		var els = QSA('#treeul li>a+a');
		for (var a = els.length - 1; a >= 0; a--)
			if (ptn.exec(els[a].textContent) && !els[a].className)
				els[a].closest('ul').removeChild(els[a].closest('li'));
	};

	r.rendertree = function (res, ts, top0, dst, rst) {
		var cur = ebi('treeul').getAttribute('ts');
		if (cur && parseInt(cur) > ts + 20 && QS('#treeul>li>a+a')) {
			console.log("reject tree; " + cur + " / " + (ts - cur));
			return;
		}
		ebi('treeul').setAttribute('ts', ts);

		if (SR && !top0) {
			var x = SR.slice(1).split('/');
			while (x[0]) {
				res = res['k' + x.shift()];
				if (!res)
					throw 'invalid --rp-loc (or bug?)';
			}
		}

		var top = (top0 == '.' ? dst : top0).split('?')[0],
			name = uricom_dec(top.split('/').slice(-2)[0]),
			rtop = top.replace(/^\/+/, ""),
			html = parsetree(res, rtop.slice(SR.length));

		if (!top0) {
			html = '<li><a href="#">-</a><a href="' + SR + '/">[root]</a>\n<ul>' + html;
			if (rst || !ebi('treeul').getElementsByTagName('li').length)
				ebi('treeul').innerHTML = html + '</ul></li>';
		}
		else {
			html = '<a href="#">-</a><a href="' +
				esc(top) + '">' + esc(name) +
				"</a>\n<ul>\n" + html + "</ul>";

			var links = QSA('#treeul a+a');
			for (var a = 0, aa = links.length; a < aa; a++) {
				if (links[a].getAttribute('href').split('?')[0] == top) {
					var o = links[a].parentNode;
					if (!o.getElementsByTagName('li').length)
						o.innerHTML = html;
				}
			}
		}
		qsr('#dlt_t');

		try {
			QS('#treeul>li>a+a').textContent = '[root]';
		}
		catch (ex) {
			console.log('got no root yet');
			r.dir_cb = null;
			return;
		}

		reload_tree();
		var fun = r.dir_cb;
		if (fun) {
			r.dir_cb = null;
			try {
				fun();
			}
			catch (ex) {
				console.log("dir_cb failed", ex);
			}
		}
	};

	function reload_tree() {
		var cevp = get_evpath(),
			cdir = r.nextdir || uricom_dec(cevp),
			links = QSA('#treeul a+a'),
			nowrap = QS('#tree.nowrap') && QS('#hovertree.on'),
			act = null;

		for (var a = 0, aa = links.length; a < aa; a++) {
			var qhref = links[a].getAttribute('href'),
				ehref = qhref.split('?')[0],
				href = uricom_dec(ehref),
				cl = '';

			if (dk && ehref == cevp && !/[?&]k=/.exec(qhref))
				links[a].setAttribute('href', addq(qhref, 'k=' + dk));

			if (href == cdir) {
				act = links[a];
				cl = 'hl';
			}
			else if (cdir.startsWith(href)) {
				cl = 'par';
			}

			links[a].className = cl;
			links[a].onclick = r.treego;
			links[a].onmouseenter = nowrap ? menter : null;
			links[a].onmouseleave = nowrap ? mleave : null;
		}
		links = QSA('#treeul li>a:first-child');
		for (var a = 0, aa = links.length; a < aa; a++) {
			links[a].setAttribute('dst', links[a].nextSibling.getAttribute('href'));
			links[a].onclick = treegrow;
		}
		ebi('tree').onscroll = nowrap ? unmenter : null;
		r.pdir = [];
		try {
			while (act) {
				r.pdir.unshift([-1, act]);
				act = act.parentNode.parentNode.closest('li').querySelector('a:first-child+a');
			}
		}
		catch (ex) { }
		r.pdir.shift();
		r.pdirw = -1;
		onresize();
	}

	function compy() {
		for (var a = 0; a < r.pdir.length; a++)
			r.pdir[a][0] = r.pdir[a][1].offsetTop;

		var ofs = 0;
		for (var a = 0; a < r.pdir.length - 1; a++) {
			ofs += r.pdir[a][1].offsetHeight + 1;
			r.pdir[a + 1][0] -= ofs;
		}
	}

	function menter(e) {
		var p = this.offsetParent,
			pp = p.offsetParent,
			ppy = pp.offsetTop,
			y = this.offsetTop + p.offsetTop + ppy - p.scrollTop - pp.scrollTop - (ppy ? document.documentElement.scrollTop : 0);

		this.style.top = y + 'px';
		this.style.position = 'fixed';
		mentered = this;
	}

	function mleave(e) {
		this.style.position = '';
		mentered = null;
	}

	function bad_proxy(e) {
		if (ctrl(e))
			return true;

		ev(e);
		var dst = this.getAttribute('dst'),
			k = dst ? 'dst' : 'href',
			v = dst ? dst : this.getAttribute('href'),
			els = QSA('#treeul a');

		for (var a = 0, aa = els.length; a < aa; a++)
			if (els[a].getAttribute(k) === v)
				return els[a].click();
	}

	r.treego = function (e) {
		if (ctrl(e))
			return true;

		ev(e);
		if (this.className == 'hl' &&
			this.previousSibling.textContent == '-') {
			treegrow.call(this.previousSibling, e);
			return;
		}
		var href = this.getAttribute('href');
		r.reqls(href, true);
		r.dir_cb = tree_scrollto;
		thegrid.setvis(true);
		clmod(this, 'ld', 1);
	}

	r.reqls = function (url, hpush, back, hydrate) {
		if (IE && !history.pushState)
			return location = url;

		var xhr = new XHR(),
			m = /[?&](k=[^&#]+)/.exec(url),
			k = m ? '&' + m[1] : dk ? '&k=' + dk : '',
			uq = (r.dots ? '&dots' : '') + k;

		if (rtt !== null)
			uq += '&rtt=' + rtt;

		xhr.top = url.split('?')[0];
		xhr.back = back
		xhr.hpush = hpush;
		xhr.hydrate = hydrate;
		xhr.ts = r.busied = Date.now();
		xhr.open('GET', xhr.top + '?ls' + uq, true);
		xhr.setRequestHeader('Fnugg', '' + xhr.ts);
		xhr.onload = xhr.onerror = recvls;
		xhr.send();

		r.nvis = r.lim;
		r.sb_msg = false;
		r.nextdir = xhr.top;
		clearTimeout(mpl.t_eplay);
		enspin('t');
		enspin('f');
		window.removeEventListener('scroll', r.tscroll);
	}

	function treegrow(e) {
		ev(e);
		if (this.textContent == '-') {
			while (this.nextSibling.nextSibling) {
				var rm = this.nextSibling.nextSibling;
				rm.parentNode.removeChild(rm);
			}
			this.textContent = '+';
			onresize();
			return;
		}
		var dst = this.getAttribute('dst');
		get_tree('.', dst);
	}

	function recvls() {
		if (!xhrchk(this, L.fl_xe1, L.fl_xe2))
			return;

		rtt = Date.now() - this.ts;

		r.nextdir = null;
		var cdir = get_evpath(),
			lfiles = ebi('files'),
			cur = lfiles.getAttribute('ts');

		if (cur && parseInt(cur) > this.ts) {
			console.log("reject ls");
			return;
		}
		lfiles.setAttribute('ts', this.ts);

		try {
			var res = JSON.parse(this.responseText);
			Object.assign(res, res.cfg);
			res.cfg.k;
		}
		catch (ex) {
			if (r.ls_cb) {
				r.ls_cb = null;
				return toast.inf(10, L.mm_nof);
			}

			if (!this.hydrate) {
				location = this.top;
				return;
			}

			return toast.err(30, "bad <code>?ls</code> reply;\nexpected json, got this:\n\n" + esc(this.responseText + ''));
		}

		if (r.chk_index_html(this.top, res))
			return;

		if (this.ts != res.fnugg && res.fnugg != 'nei' && sread('no_fnugg') !== '1')
			toast.warn(60, "WARNING: A proxy/CDN between your webbrowser and the server is misbehaving, and caching responses it shouldn't. As a result, you are now seeing stale directory listings. There will be many issues.\n\nIf you need to ignore this and stop these messages, you can set the global-option 'no-fnugg' on the server, or click <code>π</code> and run this: <code>STG.no_fnugg=1</code>");

		for (var a = 0; a < res.files.length; a++)
			if (res.files[a].tags === undefined)
				res.files[a].tags = {};

		dnsort = res.dnsort;
		read_dsort(res.dsort);
		dcrop = res.dcrop;
		dth3x = res.dth3x;
		dk = res.dk;

		srvinf = res.srvinf;
		if (rtt !== null)
			srvinf += (srvinf ? '</span> // <span>rtt: ' : 'rtt: ') + rtt;

		var o = ebi('srv_info2');
		if (o)
			o.innerHTML = ebi('srv_info').innerHTML = '<span>' + srvinf + '</span>';

		if (res.ufavico && (!favico.en || !ebi('icot').value)) {
			while (qsr('head>link[rel~="icon"]')) { }
			document.head.insertAdjacentHTML('beforeend', res.ufavico);
		}

		if (this.hpush && !showfile.active())
			hist_push(this.top + (dk ? '?k=' + dk : ''));

		if (!this.back) {
			var dirs = [];
			for (var a = 0; a < res.dirs.length; a++) {
				var dh = res.dirs[a].href,
					dn = dh.split('/')[0].split('?')[0],
					m = /[?&](k=[^&#]+)/.exec(dh);

				if (m)
					dn += '?' + m[1];

				dirs.push(dn);
			}

			r.rendertree({ "a": dirs }, this.ts, ".", get_evpath() + (dk ? '?k=' + dk : ''));
			if (res.unlist)
				r.prunetree(res);
		}

		r.gentab(this.top, res);
		qsr('#dlt_t');
		qsr('#dlt_f');

		var lg0 = res.logues ? res.logues[0] || "" : "",
			lg1 = res.logues ? res.logues[1] || "" : "",
			mds = res.readmes && treectl.ireadme,
			md0 = mds ? res.readmes[0] || "" : "",
			md1 = mds ? res.readmes[1] || "" : "",
			dirchg = get_evpath() != cdir;

		if (lg1 === Ls.eng.f_empty)
			lg1 = L.f_empty;

		sandbox(ebi('pro'), sb_lg, sba_lg,'', lg0);
		if (dirchg)
			sandbox(ebi('epi'), sb_lg, sba_lg, '', lg1);

		clmod(ebi('pro'), 'mdo');
		clmod(ebi('epi'), 'mdo');

		if (md0)
			show_readme(md0, 0);

		if (md1)
			show_readme(md1, 1);
		else if (!dirchg)
			sandbox(ebi('epi'), sb_lg, sba_lg, '', lg1);

		if (this.hpush && !this.back) {
			var ofs = ebi('wrap').offsetTop;
			if (document.documentElement.scrollTop > ofs)
				document.documentElement.scrollTop = ofs;
		}

		wintitle();
		var fun = r.ls_cb;
		if (fun) {
			r.ls_cb = null;
			fun();
		}

		if (can_shr && QS('#op_unpost.act') && (cdir.startsWith(SR + have_shr) || get_evpath().startsWith(SR + have_shr)))
			goto('unpost');
	}

	r.chk_index_html = function (top, res) {
		if (!r.idxh || !res || !res.files || noih)
			return;

		for (var a = 0; a < res.files.length; a++)
			if (/^index.html?(\?|$)/i.exec(res.files[a].href)) {
				location = vjoin(top, res.files[a].href);
				return true;
			}
	};

	r.gentab = function (top, res) {
		showfile.untail();
		var nodes = res.dirs.concat(res.files),
			html = mk_files_header(res.taglist),
			sel = msel.hist[top],
			ae = document.activeElement,
			cid = null,
			plain = [],
			seen = {};

		if (ae && /^tr$/i.exec(ae.nodeName))
			if (ae = ae.querySelector('a[id]'))
				cid = ae.getAttribute('id');

		var m = /[?&]k=([^&]+)/.exec(location.search);
		if (m)
			memo_dk(top, m[1]);

		r.lsc = res;
		if (res.unlist) {
			var ptn = new RegExp(res.unlist);
			for (var a = nodes.length - 1; a >= 0; a--)
				if (ptn.exec(uricom_dec(nodes[a].href.split('?')[0])))
					nodes.splice(a, 1);
		}
		nodes = sortfiles(nodes);
		window.removeEventListener('scroll', r.tscroll);
		r.trunc = nodes.length > r.nvis && location.hash.length < 2;
		if (r.trunc) {
			for (var a = r.lim; a < nodes.length; a++) {
				var tn = nodes[a],
					tns = Object.keys(tn.tags || {});

				plain.push(uricom_dec(tn.href.split('?')[0]));

				for (var b = 0; b < tns.length; b++)
					if (has(res.taglist, tns[b]))
						plain.push(tn.tags[tns[b]]);
			}
			nodes = nodes.slice(0, r.nvis);
		}

		showfile.files = [];
		html.push('<tbody>');
		for (var a = 0; a < nodes.length; a++) {
			var tn = nodes[a],
				bhref = tn.href.split('?')[0],
				fname = uricom_dec(bhref),
				hname = esc(fname),
				id = 'f-' + ('00000000' + crc32(fname)).slice(-8),
				lang = showfile.getlang(fname);

			while (seen[id])  // ejyefs ev69gg y9j8sg .opus
				id += 'a';
			seen[id] = 1;

			if (lang) {
				showfile.files.push({ 'id': id, 'name': fname });
				if (lang == 'md')
					tn.href = addq(tn.href, 'v');
			}

			if (tn.lead == '-')
				tn.lead = '<a href="?doc=' + bhref + '" id="t' + id +
					'" rel="nofollow" class="doc' + (lang ? ' bri' : '') +
					'" hl="' + id + '" name="' + hname + '">-txt-</a>';

			var cl = /\.PARTIAL$/.exec(fname) ? ' class="fade"' : '',
				ln = ['<tr' + cl + '><td>' + tn.lead + '</td><td><a href="' +
					top + tn.href + '" id="' + id + '">' + hname +
					'</a></td><td sortv="' + tn.sz + '">' + filesizefun(tn.sz)];

			for (var b = 0; b < res.taglist.length; b++) {
				var k = esc(res.taglist[b]),
					v = (tn.tags || {})[k] || "",
					sv = null;

				if (k == ".dur")
					sv = v ? s2ms(v) : "";
				else if (k == ".up_at")
					sv = v ? unix2ui(v) : "";
				else {
					ln.push(esc('' + v));
					continue;
				}
				ln[ln.length - 1] += '</td><td sortv="' + v + '">' + sv;
			}
			ln = ln.concat([tn.ext, unix2ui(tn.ts)]).join('</td><td>');
			html.push(ln + '</td></tr>');
		}
		html.push('</tbody>');
		html = html.join('\n');
		set_files_html(html);
		if (r.trunc) {
			r.setlazy(plain);
			if (!r.ask) {
				window.addEventListener('scroll', r.tscroll);
				setTimeout(r.tscroll, 100);
			}
		}
		else ebi('lazy').innerHTML = '';

		function asdf() {
			showfile.mktree();
			mukey.render();
			reload_tree();
			reload_browser();
			tree_scrollto();
			if (res.acct) {
				acct = res.acct;
				have_up2k_idx = res.idx;
				have_tags_idx = res.itag;
				lifetime = res.lifetime;
				apply_perms(res);
				fileman.render();
			}
			msel.loadsel(top, sel);

			if (cid) try {
				ebi(cid).closest('tr').focus();
			} catch (ex) { }

			setTimeout(eval_hash, 1);
		}

		var m = scan_hash(hash0),
			url = null;

		if (m) {
			url = ebi(m[1]);
			if (url) {
				url = url.href;
				var mt = m[0] == 'a' ? 'audio' : /\.(webm|mkv)($|\?)/i.exec(url) ? 'video' : 'image'
				if (mt == 'image') {
					url = addq(url, 'cache');
					console.log(url);
					new Image().src = url;
				}
			}
		}

		if (url) setTimeout(asdf, 1); else asdf();
	}

	r.hydrate = function () {
		qsr('#bbsw');
		srvinf = ebi('srv_info').innerHTML.slice(6, -7);
		if (ls0 === null) {
			var xhr = new XHR();
			xhr.open('GET', SR + '/?setck=js=y', true);
			xhr.send();

			r.ls_cb = showfile.addlinks;
			return r.reqls(get_evpath(), false, undefined, true);
		}
		ls0.unlist = unlist0;
		ls0.u2ts = u2ts;

		var top = get_evpath();
		if (r.chk_index_html(top, ls0))
			return;

		r.gentab(top, ls0);
		pbar.onresize();
		vbar.onresize();
		showfile.addlinks();
		setTimeout(eval_hash, 1);
	};

	function memo_dk(vp, k) {
		dks[vp] = k;
		var lv = vp + "?" + k;
		if (has(ldks, lv))
			return;

		ldks.unshift(lv);
		if (ldks.length > 32) {
			var keep = [], evp = get_evpath();
			for (var a = 0; a < ldks.length; a++) {
				var s = ldks[a];
				if (evp.startsWith(s.replace(/\?[^?]+$/, '')))
					keep.push(s);
			}
			var lim = 32 - keep.length;
			for (var a = 0; a < lim; a++) {
				if (!has(keep, ldks[a]))
					keep.push(ldks[a])
			}
			ldks = keep;
		}
		jwrite('dks', ldks);
	}

	r.setlazy = function (plain) {
		var html = ['<div id="plazy">', esc(plain.join(' ')), '</div>'],
			all = r.lsc.files.length + r.lsc.dirs.length,
			nxt = r.nvis * 4;

		if (r.ask)
			html.push((nxt >= all ? L.fbd_all : L.fbd_more).format(r.nvis, all, nxt));

		ebi('lazy').innerHTML = html.join('\n');

		try {
			ebi('bd_all').onclick = function (e) {
				ev(e);
				r.showmore(all);
			};
			ebi('bd_more').onclick = function (e) {
				ev(e);
				r.showmore(nxt);
			};
		}
		catch (ex) { }
	};

	r.showmore = function (n) {
		window.removeEventListener('scroll', r.tscroll);
		console.log('nvis {0} -> {1}'.format(r.nvis, n));
		r.nvis = n;
		ebi('lazy').innerHTML = '';
		ebi('wrap').style.opacity = 0.4;
		document.documentElement.scrollLeft = 0;
		setTimeout(function () {
			r.gentab(get_evpath(), r.lsc);
			ebi('wrap').style.opacity = CLOSEST ? 'unset' : 1;
		}, 1);
	};

	r.tscroll = function () {
		var el = r.trunc ? ebi('plazy') : null;
		if (!el || ebi('lazy').style.display || ebi('unsearch'))
			return;

		var sy = yscroll() + window.innerHeight,
			ty = el.offsetTop;

		if (sy <= ty)
			return;

		window.removeEventListener('scroll', r.tscroll);

		var all = r.lsc.files.length + r.lsc.dirs.length;
		if (r.nvis * 16 <= all) {
			console.log("{0} ({1} * 16) <= {2}".format(r.nvis * 16, r.nvis, all));
			r.showmore(r.nvis * 4);
		}
		else {
			console.log("{0} ({1} * 16) > {2}".format(r.nvis * 16, r.nvis, all));
			r.showmore(all);
		}
	};

	function parsetree(res, top) {
		var ret = '';
		for (var a = 0; a < res.a.length; a++) {
			if (res.a[a] !== '')
				res['k' + res.a[a]] = 0;
		}
		delete res['a'];
		var keys = Object.keys(res);
		for (var a = 0; a < keys.length; a++)
			keys[a] = [uricom_dec(keys[a]), keys[a]];

		if (ENATSORT)
			keys.sort(function (a, b) { return NATSORT.compare(a[0], b[0]); });
		else
			keys.sort(function (a, b) { return a[0].localeCompare(b[0]); });

		for (var a = 0; a < keys.length; a++) {
			var kk = keys[a][1],
				m = /(\?k=[^\n]+)/.exec(kk),
				kdk = m ? m[1] : '',
				ks = kk.replace(kdk, '').slice(1),
				ded = ks.endsWith('\n'),
				k = uricom_sdec(ded ? ks.replace(/\n$/, '') : ks),
				hek = esc(k[0]),
				uek = k[1] ? uricom_enc(k[0], true) : k[0],
				url = '/' + (top ? top + uek : uek) + '/',
				sym = res[kk] ? '-' : '+',
				link = '<a href="#">' + sym + '</a><a href="' +
					SR + url + kdk + '">' + hek + '</a>';

			if (res[kk]) {
				var subtree = parsetree(res[kk], url.slice(1));
				ret += '<li>' + link + '\n<ul>\n' + subtree + '</ul></li>\n';
			}
			else {
				ret += (ded ? '<li class="offline">' : '<li>') + link + '</li>\n';
			}
		}
		return ret;
	}

	function scaletree(e) {
		ev(e);
		treesz += parseInt(this.getAttribute("step"));
		if (!isNum(treesz))
			treesz = 16;

		treesz = clamp(treesz, 2, 120);
		swrite('treesz', treesz);
		onresize();
	}

	ebi('entree').onclick = r.entree;
	ebi('detree').onclick = r.detree;
	ebi('visdir').onclick = tree_scrollto;
	ebi('twig').onclick = scaletree;
	ebi('twobytwo').onclick = scaletree;

	var cs = sread('entreed'),
		vw = window.innerWidth / parseFloat(getComputedStyle(document.body)['font-size']);

	if (cs == 'tree' || (cs != 'na' && vw >= 60))
		r.entree(null, true);

	r.onpopfun = function (e) {
		console.log("h-pop " + e.state);
		if (!e.state)
			return;

		var url = new URL(e.state, "https://" + location.host),
			req = url.pathname,
			hbase = req,
			cbase = location.pathname,
			mdoc = /[?&]doc=/.exec('' + url),
			mdk = /[?&](k=[^&#]+)/.exec('' + url);

		if (mdoc && hbase == cbase)
			return showfile.show(hbase + showfile.sname(url.search), true);

		if (mdk)
			req += '?' + mdk[1];

		r.goto(req, false, true);
	};

	var evp = get_evpath() + (dk ? '?k=' + dk : '');
	hist_replace(evp + location.hash);
	r.onscroll = onscroll;
	return r;
})();


function enspin(i) {
	i = 'dlt_' + i;
	if (ebi(i))
		return;
	var d = mknod('div', i, SPINNER);
	d.className = 'dumb_loader_thing';
	if (SPINNER_CSS)
		d.style.cssText = SPINNER_CSS;
	document.body.appendChild(d);
}


var wfp_debounce = (function () {
	var r = { 'n': 0, 't': 0 };

	r.hide = function () {
		if (!sb_lg && !sb_md)
			return;

		if (++r.n <= 1) {
			r.n = 1;
			clearTimeout(r.t);
			r.t = setTimeout(r.reset, 300);
			ebi('wfp').style.opacity = 0.1;
		}
	};
	r.show = function () {
		if (!sb_lg && !sb_md)
			return;

		if (--r.n <= 0) {
			r.n = 0;
			clearTimeout(r.t);
			ebi('wfp').style.opacity = CLOSEST ? 'unset' : 1;
		}
	};
	r.reset = function () {
		r.n = 0;
		r.show();
	};
	return r;
})();


function apply_perms(res) {
	perms = res.perms || [];

	var axs = [],
		aclass = '>',
		chk = ['read', 'write', 'move', 'delete', 'get', 'admin'];

	if (konmai < 0) {
		acct = 'Ted Faro';
		srvinf = 'FAS Nexus</span> // <span>57.3 EiB free of 127 EiB';
		res.shr_who = 'auth';
		perms = res.perms = chk;
		have_up2k_idx = have_tags_idx = 1;
		have_mv = have_del = true;
	}

	var a = QS('#ops a[data-dest="up2k"]');
	if (have_up2k_idx) {
		a.removeAttribute('data-perm');
		a.setAttribute('tt', L.ot_u2i);
	}
	else {
		a.setAttribute('data-perm', 'write');
		a.setAttribute('tt', L.ot_u2w);
	}
	clmod(ebi('srch_form'), 'tags', have_tags_idx);

	a.style.display = '';
	tt.att(QS('#ops'));

	for (var a = 0; a < chk.length; a++)
		if (has(perms, chk[a]))
			axs.push(chk[a].slice(0, 1).toUpperCase() + chk[a].slice(1));

	axs = axs.join('-');
	if (perms.length == 1) {
		aclass = ' class="warn">';
		axs += '-Only';
	}

	var dst = "?h";
	if (idp_login && acct == "*")
		dst = idp_login.replace(/\{dst\}/g, get_evpath());

	ebi('acc_info').innerHTML = '<span id="srv_info2"><span>' + srvinf +
		'</span></span><span' + aclass + axs + L.access + '</span>' + (acct != '*' ?
			'<form id="flogout" method="post" enctype="multipart/form-data"><input type="hidden" name="act" value="logout" /><input id="blogout" type="submit" value="' + L.logout + acct + '"></form>' :
			'<a href="' + dst + '">' + L.login + '</a>');

	var o = QSA('#ops>a[data-perm]');
	for (var a = 0; a < o.length; a++) {
		var display = '';
		var needed = o[a].getAttribute('data-perm').split(' ');
		for (var b = 0; b < needed.length; b++) {
			if (!has(perms, needed[b])) {
				display = 'none';
			}
		}
		o[a].style.display = display;
	}

	var o = QSA('#ops>a[data-dep], #u2conf td[data-dep]');
	for (var a = 0; a < o.length; a++)
		o[a].style.display = (
			o[a].getAttribute('data-dep') != 'idx' || have_up2k_idx
		) ? '' : 'none';

	var act = QS('#ops>a.act');
	if (act && act.style.display === 'none')
		goto();

	document.body.setAttribute('perms', perms.join(' '));

	var have_write = has(perms, "write"),
		have_read = has(perms, "read"),
		de = document.documentElement,
		tds = QSA('#u2conf td');

	shr_who = res.shr_who || shr_who;
	can_shr = acct != '*' && (have_read || have_write) && (
		(shr_who == 'a' && has(perms, 'admin')) ||
		(shr_who == 'auth'));

	clmod(de, "read", have_read);
	clmod(de, "write", have_write);
	clmod(de, "nread", !have_read);
	clmod(de, "nwrite", !have_write);

	for (var a = 0; a < tds.length; a++) {
		tds[a].style.display =
			(have_write || tds[a].getAttribute('data-perm') == 'read') ?
				'table-cell' : 'none';
	}
	if (res.frand)
		ebi('u2rand').parentNode.style.display = 'none';

	u2ts = res.u2ts;
	if (up2k)
		up2k.set_fsearch();

	widget.setvis();
	thegrid.setvis();
	if (!have_read && have_write)
		goto('up2k');
}


function tr2id(tr) {
	try {
		return tr.cells[1].querySelector('a[id]').getAttribute('id');
	}
	catch (ex) {
		return null;
	}
}


function find_file_col(txt) {
	var i = -1,
		min = false,
		tds = ebi('files').tHead.getElementsByTagName('th');

	for (var a = 0; a < tds.length; a++) {
		var spans = tds[a].getElementsByTagName('span');
		if (spans.length && spans[0].textContent == txt) {
			min = (tds[a].className || '').indexOf('min') !== -1;
			i = a;
			break;
		}
	}

	if (i == -1)
		return;

	return [i, min];
}


function mk_files_header(taglist) {
	var html = [
		'<thead><tr>',
		'<th name="lead"><span>c</span></th>',
		'<th name="href"><span>File Name</span></th>',
		'<th name="sz" sort="int"><span>Size</span></th>'
	];
	for (var a = 0; a < taglist.length; a++) {
		var tag = taglist[a],
			c1 = tag.slice(0, 1).toUpperCase();

		tag = esc(c1 + tag.slice(1));
		if (c1 == '.')
			tag = '<th name="tags/' + tag + '" sort="int"><span>' + tag.slice(1);
		else
			tag = '<th name="tags/' + tag + '"><span>' + tag;

		html.push(tag + '</span></th>');
	}
	html = html.concat([
		'<th name="ext"><span>T</span></th>',
		'<th name="ts"><span>Date</span></th>',
		'</tr></thead>',
	]);
	return html;
}


var filecols = (function () {
	var r = { 'picking': false };
	var hidden = jread('filecols', []);

	r.add_btns = function () {
		var ths = QSA('#files>thead th>span');
		for (var a = 0, aa = ths.length; a < aa; a++) {
			var th = ths[a].parentElement,
				toh = ths[a].outerHTML, // !ff10
				ttv = L.cols[ths[a].textContent];

			ttv = (ttv ? ttv + '; ' : '') + 'id=<code>' + th.getAttribute('name') + '</code>';
			if (!MOBILE && toh) {
				th.innerHTML = '<div class="cfg"><a href="#">-</a></div>' + toh;
				th.getElementsByTagName('a')[0].onclick = ev_row_tgl;
			}
			if (ttv) {
				th.setAttribute("tt", ttv);
				th.setAttribute("ttd", "u");
				th.setAttribute("ttm", "12");
			}
		}
	};

	function hcols_click(e) {
		ev(e);
		var t = e.target;
		if (t.tagName != 'A')
			return;

		r.toggle(t.textContent);
	}

	r.uivis = function () {
		var hcols = ebi('hcols');
		hcols.previousSibling.style.display = hcols.style.display = ((!thegrid || !thegrid.en) && (hidden.length || MOBILE)) ? 'block' : 'none';
	};

	r.set_style = function (unhide) {
		hidden.sort();

		if (!unhide)
			unhide = [];

		var html = [],
			hcols = ebi('hcols');

		for (var a = 0; a < hidden.length; a++) {
			var ttv = L.cols[hidden[a]],
				tta = ttv ? ' tt="' + ttv + '">' : '>';

			html.push('<a href="#" class="btn"' + tta + esc(hidden[a]) + '</a>');
		}
		hcols.innerHTML = html.join('\n');
		hcols.onclick = hcols_click;
		r.uivis();
		r.add_btns();

		var ohidden = [],
			ths = QSA('#files>thead th'),
			ncols = ths.length;

		for (var a = 0; a < ncols; a++) {
			var span = ths[a].getElementsByTagName('span');
			if (span.length <= 0)
				continue;

			var name = span[0].textContent,
				cls = false;

			if (has(hidden, name) && !has(unhide, name)) {
				ohidden.push(a);
				cls = true;
			}
			clmod(ths[a], 'min', cls)
		}
		for (var a = 0; a < ncols; a++) {
			var cls = has(ohidden, a) ? 'min' : '',
				tds = QSA('#files>tbody>tr>td:nth-child(' + (a + 1) + ')');

			for (var b = 0, bb = tds.length; b < bb; b++)
				tds[b].className = cls;
		}
		if (tt) {
			tt.att(ebi('hcols'));
			tt.att(QS('#files>thead'));
		}
	};

	r.setvis = function (name, vis) {
		var ofs = hidden.indexOf(name);
		if (ofs !== -1 && vis != 0)
			hidden.splice(ofs, 1);
		else if (vis != 1) {
			if (!sread("chide_ok")) {
				return modal.confirm(L.f_chide.format(name), function () {
					swrite("chide_ok", 1);
					r.toggle(name);
				}, null);
			}
			hidden.push(name);
		}
		jwrite("filecols", hidden);
		r.set_style();
	};
	r.show = function (name) { r.setvis(name, 1); };
	r.hide = function (name) { r.setvis(name, 0); };
	r.toggle = function (name) { r.setvis(name, -1); };

	ebi('hcolsr').onclick = function (e) {
		ev(e);
		r.reset(true);
	};

	if (MOBILE)
		ebi('hcolsh').onclick = function (e) {
			ev(e);
			if (r.picking)
				return r.unpick();

			var lbs = QSA('#files>thead th');
			for (var a = 0; a < lbs.length; a++) {
				lbs[a].onclick = function (e) {
					ev(e);
					if (toast.tag == 'pickhide')
						toast.hide();

					r.hide(e.target.textContent);
				};
			};
			r.picking = true;
			clmod(ebi('files'), 'hhpick', 1);
			toast.inf(0, L.cl_hpick, 'pickhide');
		};

	r.unpick = function () {
		r.picking = false;
		toast.inf(5, L.cl_hcancel);

		clmod(ebi('files'), 'hhpick');

		var lbs = QSA('#files>thead th');
		for (var a = 0; a < lbs.length; a++)
			lbs[a].onclick = null;
	};

	r.reset = function (force) {
		if (force || JSON.stringify(def_hcols) != sread('hfilecols')) {
			console.log("applying default hidden-cols");
			hidden = [];
			jwrite('hfilecols', def_hcols);
			for (var a = 0; a < def_hcols.length; a++) {
				var t = def_hcols[a];
				t = t.slice(0, 1).toUpperCase() + t.slice(1);
				if (t.startsWith("."))
					t = t.slice(1);

				if (hidden.indexOf(t) == -1)
					hidden.push(t);
			}
			jwrite("filecols", hidden);
		}
		r.set_style();
	}
	r.reset();

	try {
		var ci = find_file_col('dur'),
			i = ci[0],
			rows = ebi('files').tBodies[0].rows;

		for (var a = 0, aa = rows.length; a < aa; a++) {
			var c = rows[a].cells[i];
			if (c && c.textContent)
				c.textContent = s2ms(c.textContent);
		}
	}
	catch (ex) { }

	return r;
})();


var mukey = (function () {
	var maps = {
		"rekobo_alnum": [
			"1B ", "2B ", "3B ", "4B ", "5B ", "6B ", "7B ", "8B ", "9B ", "10B", "11B", "12B",
			"1A ", "2A ", "3A ", "4A ", "5A ", "6A ", "7A ", "8A ", "9A ", "10A", "11A", "12A"
		],
		"rekobo_classic": [
			"B  ", "F# ", "Db ", "Ab ", "Eb ", "Bb ", "F  ", "C  ", "G  ", "D  ", "A  ", "E  ",
			"Abm", "Ebm", "Bbm", "Fm ", "Cm ", "Gm ", "Dm ", "Am ", "Em ", "Bm ", "F#m", "Dbm"
		],
		"traktor_musical": [
			"B  ", "Gb ", "Db ", "Ab ", "Eb ", "Bb ", "F  ", "C  ", "G  ", "D  ", "A  ", "E  ",
			"Abm", "Ebm", "Bbm", "Fm ", "Cm ", "Gm ", "Dm ", "Am ", "Em ", "Bm ", "Gbm", "Dbm"
		],
		"traktor_sharps": [
			"B  ", "F# ", "C# ", "G# ", "D# ", "A# ", "F  ", "C  ", "G  ", "D  ", "A  ", "E  ",
			"G#m", "D#m", "A#m", "Fm ", "Cm ", "Gm ", "Dm ", "Am ", "Em ", "Bm ", "F#m", "C#m"
		],
		"traktor_open": [
			"6d ", "7d ", "8d ", "9d ", "10d", "11d", "12d", "1d ", "2d ", "3d ", "4d ", "5d ",
			"6m ", "7m ", "8m ", "9m ", "10m", "11m", "12m", "1m ", "2m ", "3m ", "4m ", "5m "
		]
	},
		defnot = 'rekobo_alnum';

	var map = {},
		html = [],
		cb = ebi('key_notation');

	for (var k in maps) {
		if (!maps.hasOwnProperty(k))
			continue;

		html.push('<option value="{0}">{0}</option>'.format(k));
		for (var a = 0; a < 24; a++)
			maps[k][a] = maps[k][a].trim();
	}
	cb.innerHTML = html.join('');

	function set_key_notation() {
		load_notation(cb.value);
		try_render();
	}

	function load_notation(notation) {
		swrite("cpp_keynot", notation);
		map = {};
		var dst = maps[notation];
		for (var k in maps)
			if (k != notation && maps.hasOwnProperty(k))
				for (var a = 0; a < 24; a++)
					if (maps[k][a] != dst[a])
						map[maps[k][a]] = dst[a];
	}

	function render() {
		var ci = find_file_col('Key');
		if (!ci)
			return;

		var i = ci[0],
			min = ci[1],
			rows = ebi('files').tBodies[0].rows;

		if (min)
			for (var a = 0, aa = rows.length; a < aa; a++) {
				var c = rows[a].cells[i];
				if (!c)
					continue;

				var v = c.getAttribute('html');
				c.setAttribute('html', map[v] || v);
			}
		else
			for (var a = 0, aa = rows.length; a < aa; a++) {
				var c = rows[a].cells[i];
				if (!c)
					continue;

				var v = c.textContent;
				c.textContent = map[v] || v;
			}
	}

	function try_render() {
		try {
			render();
		}
		catch (ex) {
			console.log("key notation failed: " + ex);
		}
	}

	var notation = sread("cpp_keynot") || defnot;
	if (!maps[notation])
		notation = defnot;

	cb.value = notation;
	cb.onchange = set_key_notation;
	load_notation(notation);

	return {
		"render": try_render
	};
})();


var light, theme, themen;
var settheme = (function () {
	var r = {},
		ax = 'abcdefghijklmnopqrstuvwx',
		tre = '🌲',
		chldr = !SPINNER_CSS && SPINNER == tre;

	r.ldr = {
		'4':['🌴'],
		'5':['🌭', 'padding:0 0 .7em .7em;filter:saturate(3)'],
		'6':['📞', 'padding:0;filter:brightness(2) sepia(1) saturate(3) hue-rotate(60deg)'],
		'7':['▲', 'font-size:3em'], //cp437
	};

	theme = sread('cpp_thm') || 'a';
	if (!/^[a-x][yz]/.exec(theme))
		theme = dtheme;

	themen = theme.split(/ /)[0];
	light = !!(theme.indexOf('y') + 1);

	function freshen() {
		var cl = document.documentElement.className;
		cl = cl.replace(/\b(light|dark|[a-z]{1,2})\b/g, '').replace(/ +/g, ' ');
		document.documentElement.className = cl + ' ' + theme + ' ';

		pbar.drawbuf();
		pbar.drawpos();
		vbar.draw();
		showfile.setstyle();
		bchrome();

		var html = [],
			cb = ebi('themes'),
			itheme = ax.indexOf(theme[0]) * 2 + (light ? 1 : 0),
			names = ['classic dark', 'classic light', 'pm-monokai', 'flat light', 'vice', 'hotdog stand', 'hacker', 'hi-con', 'phi95 dark', 'phi95'];

		for (var a = 0; a < themes; a++)
			html.push('<option value="{0}">{0} ┃ {1}</option>'.format(a, names[a] || 'custom'));

		ebi('themes').innerHTML = html.join('');
		cb.value = itheme;
		cb.onchange = r.onsel;

		if (chldr) {
			var x = r.ldr[itheme] || [tre];
			SPINNER = x[0];
			SPINNER_CSS = x[1];
		}

		bcfg_set('light', light);
	}

	r.onsel = function () {
		r.go(parseInt(ebi('themes').value));
	};

	r.go = function (i) {
		light = i % 2 == 1;
		var c = ax[Math.floor(i / 2)],
			l = light ? 'y' : 'z';
		theme = c + l + ' ' + c + ' ' + l;
		themen = c + l;
		swrite('cpp_thm', theme);
		freshen();
	};

	freshen();
	return r;
})();


var setfszf = (function () {
	function freshen() {
		var cb = ebi('fszfmt'),
			fmt = sread("fszfmt", humansize_fmts) || window.dfszf;
		if (!has(humansize_fmts, fmt))
			fmt = '1';
		window.filesizefun = window['humansize_' + fmt];
		cb.onchange = onch;
		if (cb.value != fmt)
			cb.value = fmt;
	}
	function onch(e) {
		ev(e);
		setfmt(ebi('fszfmt').value)
	}
	function setfmt(fmt) {
		swrite("fszfmt", fmt);
		freshen();
		treectl.gentab(get_evpath(), treectl.lsc);
	}
	freshen();
	return setfmt;
})();


(function () {
	function freshen() {
		lang = sread("cpp_lang", LANGS) || lang;
		var k, cb = ebi('langs'), html = [];
		for (var a = 0; a < LANGS.length; a++) {
			k = LANGS[a];
			html.push('<option value="{0}">{0} ┃ {1}</option>'.format(k, Ls[k].tt));
		}
		cb.innerHTML = html.join('');
		cb.onchange = setlang;
		cb.value = lang;
	}

	function setlang(e) {
		ev(e);
		var t = L.lang_set;
		lang = ebi('langs').value;
		L = Ls[lang];
		swrite("cpp_lang", lang);
		freshen();
		modal.confirm(L.lang_set + "\n\n" + t, location.reload.bind(location), null);
	}

	freshen();
})();


var arcfmt = (function () {
	if (!ebi('arc_fmt'))
		return { "render": function () { } };

	var html = [],
		fmts = [
			["tar", "tar", L.fz_tar],
			["pax", "tar=pax", L.fz_pax],
			["tgz", "tar=gz", L.fz_targz],
			["txz", "tar=xz", L.fz_tarxz],
			["zip", "zip", L.fz_zip8],
			["zip_dos", "zip=dos", L.fz_zipd],
			["zip_crc", "zip=crc", L.fz_zipc]
		];

	for (var a = 0; a < fmts.length; a++) {
		var k = fmts[a][0];
		html.push(
			'<span><input type="radio" name="arcfmt" value="' + k + '" id="arcfmt_' + k + '" tt="' + fmts[a][2] + '">' +
			'<label for="arcfmt_' + k + '" tt="' + fmts[a][2] + '">' + k + '</label></span>');
	}
	ebi('arc_fmt').innerHTML = html.join('\n');

	var fmt = sread("arc_fmt");
	if (!ebi('arcfmt_' + fmt))
		fmt = "zip";

	ebi('arcfmt_' + fmt).checked = true;

	function render() {
		var arg = null,
			tds = QSA('#files tbody td:first-child a');

		for (var a = 0; a < fmts.length; a++)
			if (fmts[a][0] == fmt)
				arg = fmts[a][1];

		for (var a = 0, aa = tds.length; a < aa; a++) {
			var o = tds[a], txt = o.textContent, href = o.getAttribute('href');
			if (!/^(zip|tar|pax|tgz|txz)$/.exec(txt))
				continue;

			var m = /(.*[?&])(tar|zip)([^&#]*)(.*)$/.exec(href);
			if (!m)
				throw new Error('missing arg in url');

			o.setAttribute("href", m[1] + arg + m[4]);
			o.textContent = fmt.split('_')[0];
		}
		ebi('selzip').textContent = fmt.split('_')[0];
		ebi('selzip').setAttribute('fmt', arg);

		QS('#zip1 span').textContent = fmt.split('_')[0];
		ebi('zip1').setAttribute("href",
			get_evpath() + (dk ? '?k=' + dk + '&': '?') + arg);

		if (!have_zip) {
			ebi('zip1').style.display = 'none';
			ebi('selzip').style.display = 'none';
		}
	}

	function try_render() {
		try {
			render();
		}
		catch (ex) {
			console.log("arcfmt failed: " + ex);
		}
	}

	function change_fmt(e) {
		ev(e);
		fmt = this.getAttribute('value');
		swrite("arc_fmt", fmt);
		try_render();
	}

	var o = QSA('#arc_fmt input');
	for (var a = 0; a < o.length; a++) {
		o[a].onchange = change_fmt;
	}

	return {
		"render": try_render
	};
})();


var msel = (function () {
	var r = {};
	r.sel = null;
	r.all = null;
	r.hist = {};
	r.so = null;  // selection origin
	r.pr = null;  // previous range

	r.load = function (reset) {
		if (r.sel && !reset)
			return;

		r.sel = [];
		if (r.all && r.all.length) {
			for (var a = 0; a < r.all.length; a++) {
				var ao = r.all[a];
				ao.sel = clgot(ebi(ao.id).closest('tr'), 'sel');
				if (ao.sel)
					r.sel.push(ao);
			}
			if (!reset)
				return;
		}

		r.all = [];
		var links = QSA('#files tbody td:nth-child(2) a:last-child'),
			is_srch = !!ebi('unsearch'),
			vbase = get_evpath();

		for (var a = 0, aa = links.length; a < aa; a++) {
			var qhref = links[a].getAttribute('href'),
				href = qhref.split('?')[0].replace(/\/$/, ""),
				item = {};

			item.id = links[a].getAttribute('id');
			item.sel = clgot(links[a].closest('tr'), 'sel');
			item.vp = href.indexOf('/') !== -1 ? href : vbase + href;

			if (dk) {
				var m = /[?&](k=[^&#]+)/.exec(qhref);
				item.q = m ? '?' + m[1] : '';
			}
			else item.q = '';

			r.all.push(item);
			if (item.sel)
				r.sel.push(item);

			if (!is_srch)
				links[a].closest('tr').setAttribute('tabindex', '0');
		}
	};

	r.loadsel = function (vp, sel) {
		if (!sel || !r.so || !ebi(r.so))
			r.so = r.pr = null;

		if (!sel)
			return r.origin_id(null);

		r.hist[vp] = sel;
		r.sel = [];
		r.load();

		var vsel = new Set();
		for (var a = 0; a < sel.length; a++)
			vsel.add(sel[a].vp);

		for (var a = 0; a < r.all.length; a++)
			if (vsel.has(r.all[a].vp))
				clmod(ebi(r.all[a].id).closest('tr'), 'sel', 1);

		r.selui();
	};

	r.getsel = function () {
		r.load();
		return r.sel;
	};
	r.getall = function () {
		r.load();
		return r.all;
	};
	r.selui = function (reset) {
		r.sel = null;
		if (reset)
			r.all = null;

		clmod(ebi('wtoggle'), 'sel', r.getsel().length);
		thegrid.loadsel();
		fileman.render();
		showfile.updtree();

		if (r.sel.length)
			r.hist[get_evpath()] = r.sel;
		else
			delete r.hist[get_evpath()];
	};
	r.seltgl = function (e) {
		ev(e);
		var tr = this.parentNode,
			id = tr2id(tr);

		if ((treectl.csel || !thegrid.en || thegrid.sel) && e.shiftKey && r.so && id && r.so != id) {
			var o1 = -1, o2 = -1;
			for (a = 0; a < r.all.length; a++) {
				var ai = r.all[a].id;
				if (ai == r.so)
					o1 = a;
				if (ai == id)
					o2 = a;
			}
			var st = r.all[o1].sel;
			if (o1 > o2)
				o2 = [o1, o1 = o2][0];

			if (r.pr) {
				// invert previous range, in case it was narrowed
				for (var a = r.pr[0]; a <= r.pr[1]; a++)
					clmod(ebi(r.all[a].id).closest('tr'), 'sel', !st);

				// and invert current selection if repeated
				if (r.pr[0] === o1 && r.pr[1] === o2)
					st = !st;
			}

			for (var a = o1; a <= o2; a++)
				clmod(ebi(r.all[a].id).closest('tr'), 'sel', st);

			r.pr = [o1, o2];

			if (window.getSelection)
				window.getSelection().removeAllRanges();
		}
		else {
			clmod(tr, 'sel', 't');
			r.origin_tr(tr);
		}
		r.selui();
	};
	r.origin_tr = function (tr) {
		r.so = tr2id(tr);
		r.pr = null;
	};
	r.origin_id = function (id) {
		r.so = id;
		r.pr = null;
	};
	r.evsel = function (e, fun) {
		ev(e);
		r.so = r.pr = null;
		var trs = QSA('#files tbody tr');
		for (var a = 0, aa = trs.length; a < aa; a++)
			clmod(trs[a], 'sel', fun);
		r.selui();
	}
	ebi('selall').onclick = function (e) {
		r.evsel(e, "add");
	};
	ebi('selinv').onclick = function (e) {
		r.evsel(e, "t");
	};
	ebi('selzip').onclick = function (e) {
		ev(e);
		var sel = r.getsel(),
			arg = ebi('selzip').getAttribute('fmt'),
			frm = mknod('form'),
			txt = [];

		if (dk)
			arg += '&k=' + dk;

		for (var a = 0; a < sel.length; a++)
			txt.push(vsplit(sel[a].vp)[1]);

		txt = txt.join('\n');

		frm.setAttribute('action', '?' + arg);
		frm.setAttribute('method', 'post');
		frm.setAttribute('target', '_blank');
		frm.setAttribute('enctype', 'multipart/form-data');
		frm.innerHTML = '<input name="act" value="zip" />' +
			'<textarea name="files" id="ziptxt"></textarea>';
		frm.style.display = 'none';

		qsr('#widgeti>form');
		ebi('widgeti').appendChild(frm);
		var obj = ebi('ziptxt');
		obj.value = txt;
		console.log(txt);
		frm.submit();
	};
	ebi('seldl').onclick = function (e) {
		ev(e);
		var sel = r.getsel();
		for (var a = 0; a < sel.length; a++)
			dl_file(sel[a].vp + sel[a].q);
	};
	r.render = function () {
		var tds = QSA('#files tbody td+td+td'),
			is_srch = !!ebi('unsearch');

		if (!is_srch)
			for (var a = 0, aa = tds.length; a < aa; a++)
				tds[a].onclick = r.seltgl;

		r.selui(true);
		arcfmt.render();
		fileman.render();

		var zipvis = (is_srch || !have_zip) ? 'none' : '';
		ebi('selzip').style.display = zipvis;
		ebi('zip1').style.display = zipvis;
	}
	return r;
})();


(function () {
	if (!FormData)
		return;

	var form = QS('#op_new_md>form'),
		tb = QS('#op_new_md input[name="name"]');

	form.onsubmit = function (e) {
		if (tb.value) {
			if (toast.tag == L.mk_noname)
				toast.hide();

			return true;
		}

		ev(e);
		toast.err(10, L.mk_noname, L.mk_noname);
		return false;
	};
})();


(function () {
	if (!FormData)
		return;

	var form = QS('#op_mkdir>form'),
		tb = QS('#op_mkdir input[name="name"]'),
		sf = mknod('div');

	clmod(sf, 'msg', 1);
	form.parentNode.appendChild(sf);

	form.onsubmit = function (e) {
		ev(e);
		var dn = tb.value;
		if (!dn) {
			toast.err(10, L.mk_noname, L.mk_noname);
			return false;
		}

		if (toast.tag == L.mk_noname || toast.tag == L.fd_xe1)
			toast.hide();

		clmod(sf, 'vis', 1);
		sf.textContent = 'creating "' + dn + '"...';

		var fd = new FormData();
		fd.append("act", "mkdir");
		fd.append("name", dn);

		var xhr = new XHR();
		xhr.vp = get_evpath();
		xhr.dn = dn;
		xhr.open('POST', dn.startsWith('/') ? (SR || '/') : xhr.vp, true);
		xhr.onload = xhr.onerror = cb;
		xhr.responseType = 'text';
		xhr.send(fd);

		return false;
	};

	function cb() {
		if (this.vp !== get_evpath()) {
			sf.textContent = 'aborted due to location change';
			return;
		}

		xhrchk(this, L.fd_xe1, L.fd_xe2);

		if (this.status !== 201) {
			sf.textContent = 'error: ' + hunpre(this.responseText);
			return;
		}

		tb.value = '';
		clmod(sf, 'vis');
		sf.textContent = '';

		var dn = this.getResponseHeader('X-New-Dir');
		dn = dn ? '/' + dn + '/' : uricom_enc(this.dn);
		treectl.goto(dn, true);
		tree_scrollto();
	}
})();


(function () {
	var form = QS('#op_msg>form'),
		tb = QS('#op_msg input[name="msg"]'),
		sf = mknod('div');

	clmod(sf, 'msg', 1);
	form.parentNode.appendChild(sf);

	form.onsubmit = function (e) {
		ev(e);
		clmod(sf, 'vis', 1);
		sf.textContent = 'sending...';

		var xhr = new XHR(),
			ct = 'application/x-www-form-urlencoded;charset=UTF-8';

		xhr.msg = tb.value;
		xhr.open('POST', get_evpath(), true);
		xhr.responseType = 'text';
		xhr.onload = xhr.onerror = cb;
		xhr.setRequestHeader('Content-Type', ct);
		if (xhr.overrideMimeType)
			xhr.overrideMimeType('Content-Type', ct);

		xhr.send('msg=' + uricom_enc(xhr.msg));
		return false;
	};

	function cb() {
		xhrchk(this, L.fsm_xe1, L.fsm_xe2);

		if (this.status < 200 || this.status > 202) {
			sf.textContent = 'error: ' + hunpre(this.responseText);
			return;
		}

		tb.value = '';
		clmod(sf, 'vis');
		var txt = 'sent: <code>' + esc(this.msg) + '</code>';
		if (this.status == 202)
			txt += '<br />&nbsp; got: <code>' + esc(this.responseText) + '</code>';

		sf.innerHTML = txt;
		setTimeout(function () {
			treectl.goto();
		}, 100);
	}
})();


var globalcss = (function () {
	var ret = '';
	return function () {
		if (ret)
			return ret;

		var dcs = document.styleSheets;
		for (var a = 0; a < dcs.length; a++) {
			var ds, base = '';
			try {
				base = dcs[a].href;
				if (!base)
					continue;

				ds = dcs[a].cssRules;
				base = base.replace(/[^/]+$/, '');
				for (var b = 0; b < ds.length; b++) {
					var css = ds[b].cssText.split(/\burl\(/g);
					ret += css[0];
					for (var c = 1; c < css.length; c++) {
						var m = /(^ *["']?)(.*)/.exec(css[c]),
							delim = m[1],
							ctxt = m[2],
							is_abs = /^\/|[^)/:]+:\/\//.exec(ctxt);

						ret += 'url(' + delim + (is_abs ? '' : base) + ctxt;
					}
					ret += '\n';
				}
				if (ret.indexOf('\n@import') + 1) {
					var c0 = ret.split('\n'),
						c1 = [],
						c2 = [];

					for (var a = 0; a < c0.length; a++)
						(c0[a].startsWith('@import') ? c1 : c2).push(c0[a]);

					ret = c1.concat(c2).join('\n');
				}
			}
			catch (ex) {
				console.log('could not read css', a, base);
			}
		}
		return ret;
	};
})();

var sandboxjs = (function () {
	var ret = '',
		busy = false,
		url = SR + '/.cpr/util.js?_=' + TS,
		tag = '<script src="' + url + '"></script>';

	return function () {
		if (ret || busy)
			return ret || tag;

		var xhr = new XHR();
		xhr.open('GET', url, true);
		xhr.onload = function () {
			if (this.status == 200)
				ret = '<script>' + this.responseText + '</script>';
		};
		xhr.send();
		busy = true;
		return tag;
	};
})();


function show_md(md, name, div, url, depth) {
	var errmsg = L.md_eshow + name + ':\n\n',
		now = get_evpath();

	url = url || now;
	if (url != now)
		return;

	wfp_debounce.hide();
	if (!marked) {
		if (depth) {
			clmod(div, 'raw', 1);
			div.textContent = "--[ " + name + " ]---------\r\n" + md;
			return toast.warn(10, errmsg + (WebAssembly ? 'failed to load marked.js' : 'your browser is too old'));
		}

		wfp_debounce.n--;
		return import_js(SR + '/.cpr/deps/marked.js', function () {
			show_md(md, name, div, url, 1);
		});
	}

	md_plug = {}
	md = load_md_plug(md, 'pre');
	md = load_md_plug(md, 'post', sb_md);

	var marked_opts = {
		headerPrefix: 'md-',
		breaks: !md_no_br,
		gfm: true
	};
	var ext = md_plug.pre;
	if (ext)
		Object.assign(marked_opts, ext[0]);

	try {
		clmod(div, 'mdo', 1);

		var md_html = marked.parse(md, marked_opts);
		if (!have_emp)
			md_html = DOMPurify.sanitize(md_html);

		if (sandbox(div, sb_md, sba_md, 'mdo', md_html))
			return;

		ext = md_plug.post;
		ext = ext ? [ext[0].render, ext[0].render2] : [];
		for (var a = 0; a < ext.length; a++)
			if (ext[a])
				try {
					ext[a](div);
				}
				catch (ex) {
					console.log(ex);
				}

		var els = QSA('#epi a');
		for (var a = 0, aa = els.length; a < aa; a++) {
			var href = els[a].getAttribute('href');
			if (!href.startsWith('#') || href.startsWith('#md-'))
				continue;

			els[a].setAttribute('href', '#md-' + href.slice(1));
		}
		md_th_set();
		set_tabindex();
		var hash = location.hash;
		if (hash.startsWith('#md-'))
			setTimeout(function () {
				try {
					QS(hash).scrollIntoView();
				}
				catch (ex) { }
			}, 1);
	}
	catch (ex) {
		toast.warn(10, errmsg + ex);
	}
	wfp_debounce.show();
}


function set_tabindex() {
	var els = QSA('pre');
	for (var a = 0, aa = els.length; a < aa; a++)
		els[a].setAttribute('tabindex', '0');
}


function show_readme(md, n) {
	var tgt = ebi(n ? 'epi' : 'pro');

	if (!treectl.ireadme)
		return sandbox(tgt, '', '', '', 'a');

	show_md(md, n ? 'README.md' : 'PREADME.md', tgt);
}
for (var a = 0; a < readmes.length; a++)
	if (readmes[a])
		show_readme(readmes[a], a);


function sandbox(tgt, rules, allow, cls, html) {
	if (!treectl.ireadme) {
		tgt.innerHTML = html ? L.md_off : '';
		return;
	}
	if (!rules || (html || '').indexOf('<') == -1) {
		tgt.innerHTML = html;
		clmod(tgt, 'sb');
		return false;
	}
	if (!CLOSEST) {
		tgt.textContent = html;
		clmod(tgt, 'sb');
		return false;
	}
	clmod(tgt, 'sb', 1);

	var tid = tgt.getAttribute('id'),
		hash = location.hash,
		want = '';

	if (!cls)
		wfp_debounce.hide();

	if (hash.startsWith('#md-'))
		want = hash.slice(1);

	var env = '', tags = QSA('script');
	for (var a = 0; a < tags.length; a++) {
		var js = tags[a].innerHTML;
		if (js && js.indexOf('have_up2k_idx') + 1)
			env = js.split(/\blogues *=/)[0] + 'a;';
	}

	html = '<html class="iframe ' + document.documentElement.className +
		'"><head><style>html{background:#eee;color:#000}</style><style>' + globalcss() +
		'</style><base target="_parent"></head><body id="b" class="logue ' + cls + '">' + html +
		'<script>' + env + '</script>' + sandboxjs() +
		'<script>var d=document.documentElement,TS="' + TS + '",' +
		'loc=new URL("' + location.href.split('?')[0] + '");' +
		'function say(m){window.parent.postMessage(m,"*")};' +
		'setTimeout(function(){var its=0,pih=-1,f=function(){' +
		'var ih=2+Math.min(parseInt(getComputedStyle(d).height),d.scrollHeight);' +
		'if(ih!=pih&&!isNaN(ih)){pih=ih;say("iheight #' + tid + ' "+ih,"*")}' +
		'if(++its<20)return setTimeout(f,20);if(its==20)setInterval(f,200)' +
		'};f();' +
		'window.onfocus=function(){say("igot #' + tid + '")};' +
		'window.onblur=function(){say("ilost #' + tid + '")};' +
		'window.treectl={"goto":function(a){say("goto #' + tid + ' "+(a||""))}};' +
		'var el="' + want + '"&&ebi("' + want + '");' +
		'if(el)say("iscroll #' + tid + ' "+el.offsetTop);' +
		'md_th_set();' +
		(cls == 'mdo' && md_plug.post ?
			'const x={' + md_plug.post + '};' +
			'if(x.render)x.render(ebi("b"));' +
			'if(x.render2)x.render2(ebi("b"));' : '') +
		'},1)</script></body></html>';

	var fr = mknod('iframe');
	fr.setAttribute('title', 'folder ' + tid + 'logue');
	fr.setAttribute('sandbox', rules ? 'allow-' + rules.replace(/ /g, ' allow-') : '');
	fr.setAttribute('allow', allow);
	fr.setAttribute('srcdoc', html);
	tgt.appendChild(fr);
	treectl.sb_msg = true;
	return true;
}
window.addEventListener("message", function (e) {
	if (!treectl.sb_msg)
		return;

	try {
		console.log('msg:' + e.data);
		var t = e.data.split(/ /g);
		if (t[0] == 'iheight') {
			var el = QSA(t[1] + '>iframe');
			el = el[el.length - 1];
			if (wfp_debounce.n)
				while (el.previousSibling)
					el.parentNode.removeChild(el.previousSibling);

			el.style.height = (parseInt(t[2]) + SBH) + 'px';
			el.style.visibility = CLOSEST ? 'unset' : 'block';
			wfp_debounce.show();
		}
		else if (t[0] == 'iscroll') {
			var y1 = QS(t[1]).offsetTop,
				y2 = parseInt(t[2]);
			console.log(y1, y2);
			document.documentElement.scrollTop = y1 + y2;
		}
		else if (t[0] == 'igot' || t[0] == 'ilost') {
			clmod(QS(t[1] + '>iframe'), 'focus', t[0] == 'igot');
		}
		else if (t[0] == 'imshow') {
			thegrid.imshow(e.data.slice(7));
		}
		else if (t[0] == 'goto') {
			var t = e.data.replace(/^[^ ]+ [^ ]+ /, '').split(/[?&]/)[0];
			treectl.goto(t, !!t);
		}
	} catch (ex) {
		console.log('msg-err: ' + ex);
	}
}, false);


if (sb_lg && logues.length) {
	if (logues[1] === Ls.eng.f_empty)
		logues[1] = L.f_empty;

	sandbox(ebi('pro'), sb_lg, sba_lg, '', logues[0]);
	sandbox(ebi('epi'), sb_lg, sba_lg, '', logues[1]);
}


(function () {
	try {
		var tr = ebi('files').tBodies[0].rows;
		for (var a = 0; a < tr.length; a++) {
			var td = tr[a].cells[1],
				ao = td.firstChild,
				href = noq_href(ao),
				isdir = href.endsWith('/'),
				txt = ao.textContent;

			td.setAttribute('sortv', (isdir ? '\t' : '') + txt);
		}
	}
	catch (ex) { }
})();


function ev_row_tgl(e) {
	ev(e);
	filecols.toggle(this.parentElement.parentElement.getElementsByTagName('span')[0].textContent);
}


var unpost = (function () {
	ebi('op_unpost').innerHTML = (
		L.un_m1 + ' &ndash; <a id="unpost_refresh" href="#">' + L.un_upd + '</a>' +
		'<p>' + L.un_m4 + ' <a id="unpost_ulist" href="#">' + L.un_ulist + '</a> / <a id="unpost_ucopy" href="#">' + L.un_ucopy + '</a>' +
		'<p>' + L.un_flt + ' <input type="text" id="unpost_filt" size="20" placeholder="documents/passwords" /><a id="unpost_nofilt" href="#">' + L.un_fclr + '</a></p>' +
		'<div id="unpost"></div>'
	);

	var r = {},
		ct = ebi('unpost'),
		filt = ebi('unpost_filt');

	r.files = [];
	r.me = null;

	r.load = function () {
		var me = Date.now(),
			html = [];

		function unpost_load_cb() {
			if (!xhrchk(this, L.fu_xe1, L.fu_xe2))
				return ebi('op_unpost').innerHTML = L.fu_xe1;

			try {
				var ores = JSON.parse(this.responseText);
			}
			catch (ex) {
				return ebi('op_unpost').innerHTML = '<p>' + L.badreply + ':</p>' + unpre(this.responseText);
			}

			if (ores.nou)
				html.push('<p>' + L.un_nou + '</p>');

			if (ores.noc)
				html.push('<p>' + L.un_noc + '</p>');

			var res = ores.f;

			if (res.length) {
				if (ores.of)
					html.push("<p>" + L.un_max);
				else
					html.push("<p>" + L.un_avail.format(ores.nc, ores.nu));

				html.push("<br />" + L.un_m2 + "</p>");
				html.push("<table><thead><tr><td></td><td>time</td><td>size</td><td>done</td><td>file</td></tr></thead><tbody>");
			}
			else
				html.push('-- <em>' + (filt.value ? L.un_no2 : L.un_no1) + '</em>');

			var mods = [10, 100, 1000];
			for (var a = 0; a < res.length; a++) {
				for (var b = 0; b < mods.length; b++)
					if (a % mods[b] == 0 && res.length > a + mods[b] / 10)
						html.push(
							'<tr><td></td><td colspan="3" style="padding:.5em">' +
							'<a me="' + me + '" class="n' + a + '" n2="' + (a + mods[b]) +
							'" href="#">' + L.un_next.format(Math.min(mods[b], res.length - a)) + '</a></td></tr>');

				var done = res[a].pd === undefined;
				html.push(
					'<tr><td><a me="' + me + '" class="n' + a + '" href="#">' + (done ? L.un_del : L.un_abrt) + '</a></td>' +
					'<td>' + unix2ui(res[a].at) + '</td>' +
					'<td>' + ('' + res[a].sz).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + '</td>' +
					(done ? '<td>100%</td>' : '<td>' + res[a].pd + '%</td>') +
					'<td>' + linksplit(res[a].vp).join('<span> / </span>') + '</td></tr>');
			}

			html.push("</tbody></table>");
			ct.innerHTML = html.join('\n');
			r.files = res;
			r.me = me;
		}

		var q = get_evpath() + '?ups';
		if (filt.value)
			q += '&filter=' + uricom_enc(filt.value, true);

		var xhr = new XHR();
		xhr.open('GET', q, true);
		xhr.onload = xhr.onerror = unpost_load_cb;
		xhr.send();

		ct.innerHTML = "<p><em>" + L.un_m3 + "</em></p>";
	};

	function linklist() {
		var ret = [],
			base = location.origin.replace(/\/$/, '');

		for (var a = 0; a < r.files.length; a++)
			ret.push(base + r.files[a].vp);

		return ret.join('\r\n');
	}

	function unpost_delete_cb() {
		if (this.status !== 200) {
			var msg = unpre(this.responseText);
			toast.err(9, L.un_derr + msg);
			return;
		}

		for (var a = this.n; a < this.n2; a++) {
			var o = QSA('#op_unpost a.n' + a);
			for (var b = 0; b < o.length; b++) {
				var o2 = o[b].closest('tr');
				o2.parentNode.removeChild(o2);
			}
		}
		toast.ok(5, this.responseText);

		if (!QS('#op_unpost a[me]'))
			goto_unpost();

		var fi = window.up2k && up2k.st.files;
		if (fi && fi.length < 9) {
			for (var a = 0; a < fi.length; a++) {
				var f = fi[a];
				if (!f.done && (f.rechecks || f.want_recheck) &&
					!has(up2k.st.todo.handshake, f) &&
					!has(up2k.st.busy.handshake, f)
				) {
					up2k.st.todo.handshake.push(f);
					up2k.ui.seth(f.n, 2, L.u_hashdone);
					up2k.ui.seth(f.n, 1, '📦 wait');
					up2k.ui.move(f.n, 'bz');
				}
			}
		}
	}

	ct.onclick = function (e) {
		var tgt = e.target.closest('a[me]');
		if (!tgt)
			return;

		if (!tgt.getAttribute('href'))
			return;

		ev(e);
		var ame = tgt.getAttribute('me');
		if (ame != r.me)
			return toast.err(0, L.un_f5);

		var n = parseInt(tgt.className.slice(1)),
			n2 = parseInt(tgt.getAttribute('n2') || n + 1),
			req = [];

		for (var a = n; a < n2; a++) {
			var links = QSA('#op_unpost a.n' + a);
			if (!links.length)
				continue;

			var f = r.files[a];
			if (f.k == 'u') {
				var vp = vsplit(f.vp.split('?')[0]),
					dfn = uricom_dec(vp[1]);
				for (var iu = 0; iu < up2k.st.files.length; iu++) {
					var uf = up2k.st.files[iu];
					if (uf.name == dfn && uf.purl == vp[0])
						return modal.alert(L.un_uf5);
				}
			}
			req.push(uricom_dec(f.vp.split('?')[0]));
			for (var b = 0; b < links.length; b++) {
				links[b].removeAttribute('href');
				links[b].innerHTML = '[busy]';
			}
		}

		toast.show('inf r', 0, L.un_busy.format(req.length));

		var xhr = new XHR();
		xhr.n = n;
		xhr.n2 = n2;
		xhr.open('POST', SR + '/?delete&unpost&lim=' + req.length, true);
		xhr.onload = xhr.onerror = unpost_delete_cb;
		xhr.send(JSON.stringify(req));
	};

	var tfilt = null;
	filt.oninput = function () {
		clearTimeout(tfilt);
		tfilt = setTimeout(r.load, 250);
	};

	ebi('unpost_nofilt').onclick = function (e) {
		ev(e);
		filt.value = '';
		r.load();
	};

	ebi('unpost_refresh').onclick = function (e) {
		ev(e);
		goto('unpost');
	};

	ebi('unpost_ulist').onclick = function (e) {
		ev(e);
		modal.alert(linklist());
	};

	ebi('unpost_ucopy').onclick = function (e) {
		ev(e);
		var txt = linklist();
		cliptxt(txt + '\n', function () {
			toast.inf(5, L.un_clip.format(txt.split('\n').length));
		});
	};

	return r;
})();


function goto_unpost(e) {
	unpost.load();
}


function wintitle(txt, noname) {
	if (txt === undefined)
		txt = '';

	if (s_name && !noname)
		txt = s_name + ' ' + txt;

	txt += uricom_dec(get_evpath()).slice(1, -1).split('/').pop();

	document.title = txt;
}


ebi('path').onclick = function (e) {
	if (ctrl(e))
		return true;

	var a = e.target.closest('a[href]');
	if (!a || !(a = a.getAttribute('href') + '') || !a.endsWith('/'))
		return;

	thegrid.setvis(true);
	treectl.reqls(a, true);
	return ev(e);
};


var scroll_y = -1;
var scroll_vp = '\n';
var scroll_obj = null;
function persist_scroll() {
	var obj = scroll_obj;
	if (!obj) {
		var o1 = document.getElementsByTagName('html')[0];
		var o2 = document.body;
		obj = o1.scrollTop > o2.scrollTop ? o1 : o2;
	}
	var y = obj.scrollTop;
	if (y > 0)
		scroll_obj = obj;

	scroll_y = y;
	scroll_vp = get_evpath();
}
function restore_scroll() {
	if (get_evpath() == scroll_vp && scroll_obj && scroll_obj.scrollTop < 1)
		scroll_obj.scrollTop = scroll_y;
}


ebi('files').onclick = ebi('docul').onclick = function (e) {
	if (!treectl.csel && e && (ctrl(e) || e.shiftKey))
		return true;

	if (!showfile.active())
		persist_scroll();

	var tgt = e.target.closest('a[id]');
	if (tgt && tgt.getAttribute('id').indexOf('f-') === 0 && tgt.textContent.endsWith('/')) {
		var el = treectl.find(tgt.textContent.slice(0, -1));
		if (el) {
			el.click();
			return ev(e);
		}
		treectl.reqls(tgt.getAttribute('href'), true);
		return ev(e);
	}
	if (tgt && /\.PARTIAL(\?|$)/.exec('' + tgt.getAttribute('href')) && !window.partdlok) {
		ev(e);
		modal.confirm(L.f_partial, function () {
			window.partdlok = 1;
			tgt.click();
		}, null);
	}

	tgt = e.target.closest('a[hl]');
	if (tgt) {
		var a = ebi(tgt.getAttribute('hl')),
			href = a.getAttribute('href'),
			fun = function () {
				showfile.show(href, tgt.getAttribute('lang'));
			},
			tfun = function () {
				bcfg_set('taildoc', showfile.taildoc = true);
				fun();
			},
			szs = ft2dict(a.closest('tr'))[0].sz,
			sz = parseInt(szs.replace(/[, ]/g, ''));

		if (sz < 1024 * 1024 || showfile.taildoc)
			fun();
		else
			modal.confirm(L.f_bigtxt.format(f2f(sz / 1024 / 1024, 1)), fun, function() {
				modal.confirm(L.f_bigtxt2, tfun, null)});

		return ev(e);
	}

	tgt = e.target.closest('a');
	if (tgt && tgt.closest('li.bn')) {
		thegrid.setvis(true);
		treectl.goto(tgt.getAttribute('href'), true);
		return ev(e);
	}
};


function reload_mp() {
	if (mp && mp.au) {
		mpo.au = mp.au;
		mpo.au2 = mp.au2;
		mpo.acs = mp.acs;
		mpo.fau = mp.fau;
		mpl.unbuffer();
	}
	var plays = QSA('tr>td:first-child>a.play');
	for (var a = plays.length - 1; a >= 0; a--)
		plays[a].parentNode.innerHTML = '-';

	mp = new MPlayer();
	if (mp.au && mp.au.tid && mp.au.evp == get_evpath()) {
		var el = QS('a#a' + mp.au.tid);
		if (el)
			clmod(el, 'act', 1);

		el = el && el.closest('tr');
		if (el)
			clmod(el, 'play', 1);
	}

	setTimeout(pbar.onresize, 1);
}


function reload_browser() {
	filecols.set_style();

	var parts = get_evpath().split('/'),
		rm = ebi('entree'),
		ftab = ebi('files'),
		link = '', o;

	while (rm.nextSibling)
		rm.parentNode.removeChild(rm.nextSibling);

	for (var a = 0; a < parts.length - 1; a++) {
		link += parts[a] + '/';
		var link2 = dks[link] ? addq(link, 'k=' + dks[link]) : link;

		o = mknod('a');
		o.setAttribute('href', link2);
		o.textContent = uricom_dec(parts[a]) || '/';
		ebi('path').appendChild(mknod('i'));
		ebi('path').appendChild(o);
	}

	reload_mp();
	try { showsort(ftab); } catch (ex) { }
	makeSortable(ftab, function () {
		msel.origin_id(null);
		msel.load(true);
		thegrid.setdirty();
		mp.read_order();
	});

	var ns = ['pro', 'epi', 'lazy']
	for (var a = 0; a < ns.length; a++)
		clmod(ebi(ns[a]), 'hidden', ebi('unsearch'));

	if (up2k)
		up2k.set_fsearch();

	thegrid.setdirty();
	msel.render();
}
treectl.hydrate();
