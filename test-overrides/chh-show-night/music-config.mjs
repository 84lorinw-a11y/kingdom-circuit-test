// Exact audio-only recording imported from the owner-supplied Instagram audio page.
// The bundled audio avoids relying on an expiring Instagram CDN URL.
// Approximate tempo measured from onset analysis; first playable beat is 2.58 seconds.
export const djTrack={
 title:'B–I–B–L–E',artist:'Eli Williams',handle:'@eliwilliamssss',
 reelUrl:'https://www.instagram.com/reel/DWg-H71Dj7C/',
 audioPageUrl:'https://www.instagram.com/reels/audio/26918190851106069/',
 src:'/play/assets/music/eli-bible-original.m4a',volume:1,gain:1.18,bpm:104,offsetSeconds:0,firstBeatSeconds:2.58
};

// Released preview excerpts: replace these slots when the owner supplies final music.
const previews={
 "wow": {
  "title": "WOW",
  "artist": "MARTY & Propaganda",
  "src": "/play/assets/music/marty-wow-preview.m4a",
  "listenUrl": "https://music.apple.com/us/album/wow/6785959438?i=6785959452&uo=4",
  "loop": true,
  "preview": true
 },
 "today": {
  "title": "TODAY (feat. Ryan Ellis)",
  "artist": "MARTY",
  "src": "/play/assets/music/marty-today-preview.m4a",
  "listenUrl": "https://music.apple.com/us/album/today-feat-ryan-ellis/6785959438?i=6785959451&uo=4",
  "loop": true,
  "preview": true
 },
 "everything-is-fine": {
  "title": "EVERYTHING IS FINE (im lying)",
  "artist": "MARTY & tonyxtrotter",
  "src": "/play/assets/music/marty-everything-is-fine-preview.m4a",
  "listenUrl": "https://music.apple.com/us/album/everything-is-fine-im-lying/6785959438?i=6785959447&uo=4",
  "loop": true,
  "preview": true
 },
 "father-love": {
  "title": "FATHER LOVE (feat. De'Aris)",
  "artist": "MARTY",
  "src": "/play/assets/music/marty-father-love-preview.m4a",
  "listenUrl": "https://music.apple.com/us/album/father-love-feat-dearis/6785959438?i=6785959450&uo=4",
  "loop": true,
  "preview": true
 },
 "cult-classic": {
  "title": "CULT CLASSIC",
  "artist": "MARTY",
  "src": "/play/assets/music/marty-cult-classic-preview.m4a",
  "listenUrl": "https://music.apple.com/us/album/cult-classic/6785959438?i=6785959441&uo=4",
  "loop": true,
  "preview": true
 },
 "ned-flanders": {
  "title": "NED FLANDERS",
  "artist": "MARTY & Brenno",
  "src": "/play/assets/music/marty-ned-flanders-preview.m4a",
  "listenUrl": "https://music.apple.com/us/album/ned-flanders/6785959438?i=6785959443&uo=4",
  "loop": true,
  "preview": true
 }
};
export const stageTracks={marty:previews['cult-classic'],brenno:previews['ned-flanders']};
export const merchTrack=previews['wow'];
export const crewTracks={'ryan-ellis':previews['today'],'gavin-the-hotrod':previews['wow'],'lj-the-messenger':previews['cult-classic'],dearis:previews['father-love'],tonyxtrotter:previews['everything-is-fine'],'andrew-prim':previews['cult-classic']};
export const gameTracks={eli:djTrack,...stageTracks,...crewTracks,apollo:merchTrack};
