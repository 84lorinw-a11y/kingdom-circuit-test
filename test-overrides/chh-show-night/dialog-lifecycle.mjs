// Native dialog close events are queued. An old event must never dispose a new view.
export function createDialogLifecycle(dialog,content){
 let cleanup=null;
 function clear(){const previous=cleanup;cleanup=null;previous?.();dialog.classList.remove('game-dialog','score-dialog');content.className='';delete content.dataset.game;delete content.dataset.phase;}
 return {
  prepare(){clear();content.replaceChildren();return content;},
  attach(dispose){cleanup=dispose;},
  close(){clear();dialog.close();},
  onNativeClose(){if(dialog.open)return false;clear();return true;}
 };
}
