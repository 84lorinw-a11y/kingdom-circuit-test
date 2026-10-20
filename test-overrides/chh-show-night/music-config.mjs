// Exact audio-only recording imported from the owner-supplied Instagram audio page.
// The bundled audio avoids relying on an expiring Instagram CDN URL.
// Approximate tempo measured from onset analysis; first playable beat is 2.58 seconds.
export const djTrack={
 title:'B–I–B–L–E',artist:'Eli Williams',handle:'@eliwilliamssss',
 reelUrl:'https://www.instagram.com/reel/DWg-H71Dj7C/',
 audioPageUrl:'https://www.instagram.com/reels/audio/26918190851106069/',
 src:'/play/assets/music/eli-bible-original.m4a',volume:1,gain:1.18,bpm:104,offsetSeconds:0,firstBeatSeconds:2.58
};

// Original instrumental soundcheck loops, pending the owner's album selection.
export const stageTracks={
 brenno:{title:'Soundcheck · Crew Run',artist:'Instrumental preview',src:'/play/assets/music/apollo-crew-soundcheck.wav',durationSeconds:21},
 marty:{title:'Soundcheck · Not 4 Sale',artist:'Instrumental preview',src:'/play/assets/music/apollo-record-soundcheck.wav',durationSeconds:21}
};
export const merchTrack={title:'Soundcheck · Merch Drop',artist:'Instrumental preview',src:'/play/assets/music/apollo-merch-soundcheck.wav',durationSeconds:25};

// Shared original soundchecks stand in for album tracks; no unreleased audio is bundled.
export const crewTracks=Object.fromEntries(['ryan-ellis','gavin-the-hotrod','lj-the-messenger','dearis','tonyxtrotter','andrew-prim'].map(id=>[id,{...stageTracks.brenno,title:'Original instrumental soundcheck',loop:true}]));
