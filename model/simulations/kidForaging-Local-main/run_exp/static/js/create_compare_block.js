function shuffle(a) {
    var j, x, i;
    for (i = a.length - 1; i > 0; i--) {
        j = Math.floor(Math.random() * (i + 1));
        x = a[i];
        a[i] = a[j];
        a[j] = x;
    }
    return a;
}

function parse(str) {
  console.log('parse')
    var args = [].slice.call(arguments, 1),
        i = 0;

    return str.replace(/%s/g, () => args[i++]);
}

var main_stim_string = "<img src='run_exp/static/images/task_images/aliens/old_aliens/icon/alien-%s.jpg' height='100'>"

var button_string ='<button class="jspsych-html-btn"><img src="run_exp/static/images/task_images/aliens/old_aliens/icon/alien-%s.jpg" height="200"></button>'

function create_main_stimulus(main_alien,true_planet,aliens) {
  console.log('main')
  console.log(main_alien)
  console.log('true_planet')
  console.log(true_planet)
  console.log('aliens')
  console.log(aliens)

  var isMain = (element) => element == main_alien;

  var index = true_planet.findIndex(isMain);

  console.log('index')
  console.log(index)

  console.log('aliens-index')
  console.log(aliens[index])
  console.log('parse string')
  if (aliens[index] == null) {
    console.log('null')
    return parse(main_stim_string,aliens[index])
  } else {
    console.log(' not null')

    return parse(main_stim_string,aliens[index].toString())
  }
  }

function create_buttons(compare_aliens,true_planet,aliens) {
  console.log('button')
  buttons = []
  var isButton;
  var index;
  for (var i = 0; i < 3; i++) {
    isButton = (element) => element == compare_aliens[i];
    index = true_planet.findIndex(isButton);
    console.log('index')
    console.log(index)

    if (aliens[index] == null) {
      buttons.push(parse(button_string,aliens[index]))

    } else {
      buttons.push(parse(button_string,aliens[index].toString()))
    }
    console.log('aliens-index')
    console.log(aliens[index])
  }
  return buttons
}

function create_compare_block(compare_trials,true_planet,aliens) {
  var block_timeline = []
  var n_trials = compare_trials.length
  console.log(compare_trials)
  console.log(n_trials)
  for (var i = 0; i < n_trials; i++) {
    block_timeline.push({stimulus:create_main_stimulus(compare_trials[i][0],true_planet,aliens),button_html:create_buttons(shuffle(compare_trials[i].slice(1,4)),true_planet,aliens)})
  }
  return block_timeline
}
