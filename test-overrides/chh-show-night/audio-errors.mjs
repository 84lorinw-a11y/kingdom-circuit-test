export function musicRetryMessage(error){
 const message=String(error?.message||'');
 if(error?.name==='NotAllowedError'||/enable music|did not start|resume/i.test(message))
  return 'Tap again to allow the music to start.';
 if(['AbortError','EncodingError','NetworkError'].includes(error?.name)||/fetch|network|unavailable|too long|load|offline/i.test(message))
  return 'The music couldn’t load. Check your connection, then try again.';
 return 'The music couldn’t start. Try again, or reload the game if it keeps happening.';
}
