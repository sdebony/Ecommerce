 
var header = document.getElementById("header_top");

window.addEventListener('scroll',()=> {
   
    var scroll = window.scrollY

    if (scroll>1){
        header.style.backgroundColor = '#121212'
    } else {
        header.style.backgroundColor = 'transparent'
    }
})
