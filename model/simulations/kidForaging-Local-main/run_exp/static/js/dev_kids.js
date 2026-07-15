var timeline = []

// for playiing audio
function sound(src) {
  this.sound = document.createElement("audio");
  this.sound.src = src;
  this.sound.setAttribute("preload", "auto");
  this.sound.setAttribute("controls", "none");
  this.sound.style.display = "none";
  document.body.appendChild(this.sound);
  this.play = function(){
    this.sound.play();
  }
  this.stop = function(){
    this.sound.pause();
  }
}

var num_quiz_failures = 0;
// for quiz
var correct_answers = ['C','B','B'];

// check if arrays match, for quiz checking purposes
var arraysMatch = function (arr1, arr2) {
	// Check if the arrays are the same length
  if (JSON.stringify(arr1) === JSON.stringify(arr2)) {
    return true;
  } else{
    return false
  }
};


var get_answers = function (answers_dict) {
  var answers = []
  var keys = ["Q0","Q1","Q2"]

  keys.forEach(function (item, index) {
    answers.push(answers_dict[item])
  });
  return answers
}

var image_prefix = "../static/images/task_images/";
var image_prefix_button = "<img src=../static/images/task_images/";

// default images
const decision_img = [image_prefix+"land.jpg"];
const land_img = [image_prefix+"land.jpg"]
const dig_img = [image_prefix+"dig.jpg"];
const space_treasure_img = [image_prefix+"gems/100.jpg"];
const harvest_practice_img = [image_prefix+"barrel_text.jpg"];
const travel_sequence = [image_prefix+"rocket-01.jpg",image_prefix+"rocket-02.jpg",image_prefix+"rocket-03.jpg",
image_prefix+"rocket-04.jpg",image_prefix+"rocket-05.jpg",image_prefix+"rocket-06.jpg",image_prefix+"rocket-07.jpg",
 image_prefix+"rocket-08.jpg",image_prefix+"rocket-09.jpg"];

const dig_sequence = [image_prefix+"dig.jpg",image_prefix+"land.jpg",image_prefix+"dig.jpg"];

const time_out_img = [image_prefix+"time_out.jpg"];
const catch_img = [image_prefix+"catch.jpg"];

var go_back = function(data) {
  if (data.trial_type == 'instruc_welcome') {
    jsPsych.addNodeToEndOfTimeline({timeline: [welcome,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_goal') {
    jsPsych.addNodeToEndOfTimeline({timeline: [welcome,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_dig') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_goal,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_travel') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_dig,dig_prac,instructions_travel,travel_prac,instructions_alien,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_alien_greet') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_travel,travel_prac,instructions_alien,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'time_out') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_alien,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_break') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_time_out,decision],}, jsPsych.resumeExperiment);
}}

var go_forward = function(data) {
  if (data.trial_type == 'instruc_welcome') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_goal,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_goal') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_dig,dig_prac,instructions_travel,instructions_alien,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_dig') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_travel,travel_prac,instructions_alien,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_travel') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_alien,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_alien_greet') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_time_out,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'time_out') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_break,decision],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_break') {
    jsPsych.addNodeToEndOfTimeline({timeline: [quiz_prac],}, jsPsych.resumeExperiment);
}}


var dig_prac = {
  type: 'animation',
  stimuli: dig_sequence,
  prompt: "<p style = 'color:white;'><strong>Practice Trial</strong></p> <p style = 'color:white;'>Dig here ('Q') or travel to a new planet ('P')?</p>",
  choices: jsPsych.NO_KEYS,
  frame_time: 667,
  on_start: function(dig_prac) {
    var last_trial_data = jsPsych.data.get().last(1).values()[0];
    if (last_trial_data.trial_type == "decision") {
      var adjusted_rt = 2000 - last_trial_data.rt;
      dig_prac.frame_time = adjusted_rt/3;
      var src = "../static/audio/axe.mp3#t=1.5,"
      var tt_sec = adjusted_rt/1000 + 1.5; //need to convert to seconds
      var axe_audio = new sound(src.concat(tt_sec.toString()))
      axe_audio.play()
    } else {
      var src = "../static/audio/axe.mp3#t=1.5,"
      var tt_sec = 4.5; //need to convert to seconds
      var axe_audio = new sound(src.concat(tt_sec.toString()))
      axe_audio.play()
    }
  },
	on_finish: function(data) {
		data.trial_type = "dig_prac";
	}
}

var travel_prac = {
  type: 'animation',
  stimuli: travel_sequence,
  prompt: "<p style = 'color:white;'><strong>Practice Trial</strong></p> <p style = 'color:white;'>Dig here ('Q') or travel to a new planet ('P')?</p>",
  frame_time: 889, // in milliseconds
  choices: jsPsych.NO_KEYS,
  on_start: function() {
    var last_trial_data = jsPsych.data.get().last(1).values()[0];
    var last_rt = last_trial_data.rt;
    var adjusted_travel_time = 8888 - last_rt;
    travel.frame_time = adjusted_travel_time/9;
    var src = "../static/audio/rocket.mp3#t=0,"
    var tt_sec = adjusted_travel_time/100-0.5; //need to convert to seconds
    var rocket_audio = new sound(src.concat(tt_sec.toString()))
    rocket_audio.play()
  },
  on_finish: function(data) {
    data.trial_type = "travel_prac";
    data.planet = planet;
  },
}

var welcome = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
  prompt: "<p>Howdy! In this experiment, you’ll be an explorer traveling through space to collect space treasure.</p><p>Your mission is to collect as much treasure as possible.</p><br><br><p><img src='../static/images/task_images/opening_img-01.jpg' height='300' width='auto'></p>",
  //choices: jsPsych.NO_KEYS,
  response_ends_trial: true,
  trial_ends_after_audio: false,
  on_finish: function(data) {
    data.trial_type = "instruc_welcome";
    data.prompt = "<p>Howdy! In this experiment, you’ll be an traveling through space to collect space treasure.</p><p>Your mission is to collect as much treasure as possible.</p><br><br><p><img src='../static/images/task_images/opening_img-01.jpg' height='300' width='auto'></p>";
  }
};


var instructions_goal = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
  prompt: "<p> As a space explorer, you’ll visit different planets to dig for space treasure, these pink gems.</p> <p> The more space treasure you mine, the more bonus money you’ll win! </p><br><br><p><img src='../static/images/task_images/pink_gem.jpg' height='300' width='auto'></p>",
  //choices: jsPsych.NO_KEYS,
  response_ends_trial: true,
  trial_ends_after_audio: false,
  on_finish: function(data) {
    data.trial_type = "instruc_goal";
    data.prompt = "<p> As a space explorer, you’ll visit different planets to dig for space treasure, these pink gems.</p> <p> The more space treasure you mine, the more bonus money you’ll win! </p><br><br><p><img src='../static/images/task_images/pink_gem.jpg' height='300' width='auto'></p>";

  }
};

var instructions_dig = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
  prompt: "<p> When you’ve arrived at a new planet, you will dig once. </p> <p>Then, you get to decide if you want to stay on the planet and dig again or travel to a new planet and dig there.</p> <p> To stay and dig, press the letter <strong>‘A’</strong> on the keyboard. Try pressing it now! </p><p><img src='../static/images/task_images/land.jpg'  height='700' width='auto'></p>",
  choices: ['A'],
  response_ends_trial: true,
  //trial_ends_after_audio: true,
  on_finish: function(data) {
   data.next_reward = 100.0;
   data.trial_type = "instruc_dig"
 }
};

var instructions_travel = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
  prompt: "<p> The longer you mine a planet the fewer gems you’ll get with each dig.</p><p>When gems are running low, you may want to travel to a new planet </p> <p>  Planets are far apart in this galaxy, so it will take some time to travel between them. </p> <br><p>There are lots and lots of planets for you to visit, so you won’t be able to return to any planets you’ve seen before. </p><br><p>To leave this planet and travel to a new one, press the letter <strong>‘L’</strong> on the keyboard. Try pressing it now! </p><p><img src='../static/images/task_images/rocket-01.jpg'  height='600' width='auto'></p>",
  choices: ['L'],
  response_ends_trial: true,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "instruc_travel";
    data.prompt = "<p> The longer you mine a planet the fewer gems you’ll get with each dig.</p><p>When gems are running low, you may want to travel to a new planet </p> <p>  Planets are far apart in this galaxy, so it will take some time to travel between them. </p> <br><p>There are lots and lots of planets for you to visit, so you won’t be able to return to any planets you’ve seen before. </p><br><p>To leave this planet and travel to a new one, press the letter <strong>‘L’</strong> on the keyboard. Try pressing it now! </p><p><img src='../static/images/task_images/rocket-01.jpg'  height='600' width='auto'></p>";
  }
};

var instructions_alien = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
  prompt: '<p>When you arrive at a new planet, an alien from that planet will greet you!</p><br><p><img src="../static/images/task_images/aliens/alien_planet-125.jpg"  height="700" width="auto"></p>',
  //choices: jsPsych.NO_KEYS,
  response_ends_trial: true,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "instruc_alien_greet";
    data.prompt ='<p>When you arrive at a new planet, an alien from that planet will greet you!</p><br><p><img src="../static/images/task_images/aliens/alien_planet-125.jpg"  height="700" width="auto"></p>'
  }
}

var instructions_time_out = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
  prompt: '<p>If you’re not fast enough in making a choice, you’ll have to wait a few seconds before you can make another one.</p><p>You can’t dig for more gems or travel to new planets. You just have to sit and wait.</p><br><p><img src="../static/images/task_images/time_out.jpg"  height="700" width="auto"></p>',
  //choices: jsPsych.NO_KEYS,
  response_ends_trial: true,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "time_out";
    data.prompt ='<p>If you’re not fast enough in making a choice, you’ll have to wait a few seconds before you can make another one.</p><p>You can’t dig for more gems or travel to new planets. You just have to sit and wait.</p><br><p><img src="../static/images/task_images/time_out.jpg"  height="700" width="auto"></p>';
  }
}



var instructions_break = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
	prompt:  "<p> After digging and traveling for a while (5 minutes), you’ll be able to take a break at home base. </p><p>The game will last 30 minutes no matter what.</p><p>So, you will visit home base five times during the game.</p><br><img src='../static/images/task_images/home_base.jpg' height='700' width='auto'>",
  //choices: jsPsych.NO_KEYS,
  response_ends_trial: true,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "instruc_break";
    data.prompt=  "<p> After digging and traveling for a while (5 minutes), you’ll be able to take a break at home base. </p><p>The game will last 30 minutes no matter what.</p><p>So, you will visit home base five times during the game.</p><br><img src='../static/images/task_images/home_base.jpg' height='700' width='auto'>";
  }
}

var instructions_practice_game = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/axe.mp3',
	prompt:"<p> Are you ready to play a practice game? </p> <p>In this practice game, you'll be digging up barrels of gems. But, in the real game, you'll be digging up the gems themselves. </p>",
  //choices: jsPsych.NO_KEYS,
  response_ends_trial: true,
  trial_ends_after_audio: true,
  on_finish: function(data){
    data.trial_type = "instruc_prac_game";
    data.prompt="<p> Are you ready to play a practice game? </p> <p>In this practice game, you'll be digging up barrels of gems. But, in the real game, you'll be digging up the gems themselves. </p>";
  }
}

var instructions_begin_exp = {
	 type: 'html-button-response',
	 stimulus:'<p>Now that you know how  to dig for space treasure and travel to new planets, you can start exploring! </p><p>Do you want to play the practice game again or get started with the real game?</p>',
	 choices: ['Practice game again','Move on to the real game'],
	 on_finish: function(data){
		 if (data.button_pressed == '0') {
			 jsPsych.addNodeToEndOfTimeline({
					timeline: [alien_welcome_prac,landing_prac,dig_prac,harvest_instruc,decision_prac],
				}, jsPsych.resumeExperiment);
        window.aliens_prac = [121,122,123,124];
				window.n_prac_rounds = n_prac_rounds + 1; // increase number of practice rounds they've done
				window.curr_prac_trial = 1; // reset current practice trial
		 } else {
			jsPsych.addNodeToEndOfTimeline({
				 timeline: [alien_welcome,landing,dig,harvest,decision],
			 }, jsPsych.resumeExperiment);
		 data.n_prac_rounds = n_prac_rounds;
		 window.block_start = Date.now();
		}
    data.trial_type = "instruc_begin_exp";
	 }
 };


  // to check their understanding of the instructions
   var quiz_prac = {
     type:'survey-html-form',
     html:"<p><strong>Now, I'm gonna ask you some questions to make sure you understand the game. You can't continue until you get all of them correct. </strong></p><br><br><p>How do you win extra money?</p><input type='radio' name='Q0' value='A' checked> Visiting more planets<br><input type='radio' name='Q0' value='B'>  Staying at home base longer<br><input type='radio' name='Q0' value='C'> Collecting more gems<br><br><br><br><p>The length of this experiment </p><input type='radio' name='Q1' value='A' checked> depends on how many planets you've visited.<br><input type='radio' name='Q1' value='B'>is 30 minutes no matter what. <br><input type='radio' name='Q1' value='C'> depends on how many gems you've collected.<br><br><br><br><p>You press what letter to travel to a new planet? </p><input type='radio' name='Q2' value='A' checked> A<br><input type='radio' name='Q2' value='B'> L<br> <br><br><br>",
     on_finish: function(data) {
       var answers_dict = JSON.parse(data.responses);
       data.trial_type = "quiz_prac";
       if (arraysMatch(correct_answers,get_answers(answers_dict))) {
         // yay everything correct, can move forward
         jsPsych.addNodeToEndOfTimeline({
           timeline: [quiz_correct, instructions_practice_game, alien_welcome_prac, landing_prac, dig_prac, harvest_prac, decision_prac],
         }, jsPsych.resumeExperiment);
       } else {
         // got at least one thing wrong, need to go through instructions again
         jsPsych.addNodeToEndOfTimeline({
           timeline: [quiz_incorrect,quiz_prac],
         }, jsPsych.resumeExperiment);

         window.num_quiz_failures= num_quiz_failures + 1;

       }
     }
   }

   var quiz_correct = {
     type:'survey-html-form',
     html:"<p><strong>Good job! You got all the questions correct!</strong></p><br><br><p>How do you win extra money?</p><input type='radio' name='Q0' value='A' style='color:#eb3e17;'> Visiting more planets<br><input type='radio' name='Q0' value='B' style='color:#eb3e17;'> Staying at home base longer<br><input type='radio' name='Q0' value='C' style='color:#0eb314;' checked> Collecting more gems<br><br><br><br><p>The length of this experiment </p><input type='radio' name='Q1' value='A' style='color:#eb3e17;'> depends on how many planets you've visited.<br><input type='radio' name='Q1' value='B' style='color:#0eb314;' checked>is 30 minutes no matter what. <br><input type='radio' name='Q1' value='C' style='color:#eb3e17;'> depends on how many gems you've collected.<br><br><br><br><p>You press what letter to travel to a new planet?</p><input type='radio' name='Q2' value='A' style='color:#eb3e17;'> A <br><input type='radio' name='Q2' value='B' style='color:#0eb314;' checked> L <br> <br><br><br>",
     button_label: 'continue to practice game',
     on_finish: function(data) {
       data.trial_type = 'quiz_correct';
     }
   }

 var quiz_incorrect = {
   type:'survey-html-form',
   html:"<p><strong>Oops, you missed some questions. Let's read over the instructions again!</p> <p> In this game, you will be traveling to different planets to mine for space treasure.</p>  To dig for gems on the current planet, press the letter 'A' on your keyboard. To travel to a new planet, press the letter 'L'. </p>The more gems you collect the more money you will win!</p><p> This game will take 30 minutes no matter how many gems you collect nor how many planets you visit.</p>",
   button_label: 'take the quiz again',
   on_finish: function(data) {
     data.trial_type = 'quiz_incorrect';
   }
 }


var decision = {
  type:'html-slider-response',
  stimulus: '../static/images/task_images/aliens/alien_planet-1.jpg',
  prompt:'<br>If you want to read more instructions, move the alien to the green planet. <br>If you want to re-read the instructions on the last page, move the alien to the blue planet.<br>',
  require_movement:true,
  on_start: function(decision) {
    last_trial = jsPsych.data.get().last(1).values()[0];
    //text = last_trial.prompt
    decision.stimulus = last_trial.prompt;
  },
  on_finish: function(data) {
    last_trial = jsPsych.data.get().last(1).values()[0];
    last_last_trial = jsPsych.data.get().last(2).values()[0];
    if (parseInt(last_trial.response,10) > 50) { // they want to move forward
      go_forward(last_last_trial)
    } else if (parseInt(last_trial.response,10) <= 50) { // they want to go back
      go_back(last_last_trial)
    }
  }
}

var decision = {
  type: 'image-keyboard-response',
  stimulus: decision_img,
  stimulus_height:700,
  trial_duration:2000,
  prompt:"<p>Dig here or travel to a new planet?<p>",
  choices: ['A', 'L'],
}

var dig = {
	type: 'animation',
	stimuli: dig_sequence,
  prompt: "<p style = 'color:white;'> Dig here or travel to a new planet?</p>",
  frame_time: 500,
  choices: jsPsych.NO_KEYS,
};

var aliens = [0,1,2,3]

var get_icons = function (aliens, old_aliens, new_aliens) {
  arr = []
  for (let i = 0; i < aliens.length; i++) {
    arr.push(old_aliens[aliens[i]]);
  }

  for (let i = 0; i < new_aliens.length; i++) {
    arr.push(new_aliens[i]);
  }
  return arr;
}


var sort_trial = {
    type: 'free-sort',
    stimuli:old_aliens,
    prompt: "<p>Click and drag the images below to sort them so that similar items are close together.</p>",
    sort_area_shape: "square",
    scale_factor:1.5,
    sort_area_width:1000,
    border_width:5,
    change_border_background_color: false,
    on_start: function(sort_trial) {
      sort_images = get_icons(aliens, old_aliens, new_aliens)
      sort_trial.stimuli = sort_images;
    }
};





var decision = {
type:'html-button-response',
stimulus: "<p> Are you ready to play a practice game? </p> <p>In this practice game, you'll be digging up barrels of gems. But, in the real game, you'll be digging up the gems themselves. </p>",
prompt:'<br>Click the green planet to play the practice game. Click the blue planet to re-read the instructions.<br>',
choices:['backward','forward'],
button_html:['<button class="jspsych-html-btn"><img src="../static/images/task_images/planet-01.jpg" height="50"></button>','<button class="jspsych-html-btn"><img src="../static/images/task_images/planet-02.jpg" height="50"></button>'],
margin_horizontal: '300px',
}


var begin_practice= {
type:'html-button-response',
stimulus: "<p> Are you ready to play a practice game? </p> <p>In this practice game, you'll be digging up barrels of gems. But, in the real game, you'll be digging up the gems themselves. </p>",
prompt:'<br>Click the green planet to play the practice game. Click the blue planet to re-read the instructions.<br>',
choices:['backward','forward'],
button_html:['<button class="jspsych-html-btn"><img src="../static/images/task_images/planet-01.jpg" height="50"></button>','<button class="jspsych-html-btn"><img src="../static/images/task_images/planet-02.jpg" height="50"></button>'],
margin_horizontal: '300px',
}

var instruc_dec_key = {
type:'html-keyboard-response',
stimulus: 'run_exp/static/images/task_images/aliens/instructions_aliens/planet/alien_planet-01.jpg',
choices:['space'],
on_start: function(instruc_dec_key) {
  last_trial = jsPsych.data.get().last(1).values()[0];
  if (last_trial.button_pressed == 0) {
    instruc_dec_key.stimulus = last_trial.stimulus.concat('<button class="jspsych-html-btn-chosen"><img src="../static/images/task_images/planet-01.jpg" height="50"></button><button class="jspsych-html-btn-unchosen"><img src="../static/images/task_images/planet-02.jpg" height="50"></button><p><b>[press the space bar to lock in your answer]<b><br></p>');
  } else {
    instruc_dec_key.stimulus = last_trial.stimulus.concat('<button class="jspsych-html-btn-unchosen"><img src="../static/images/task_images/planet-01.jpg" height="50"></button><button class="jspsych-html-btn-chosen"><img src="../static/images/task_images/planet-02.jpg" height="50"></button><p><b>[press the space bar to lock in your answer]<b><br></p>');}
  },
on_finish: function(data) {
  last_trial = jsPsych.data.get().last(1).values()[0];
}};

var compare_alien = {
  type:'html-button-response',
  stimulus:"<img src='../static/images/task_images/aliens/old_aliens/icon/alien-01.jpg'>",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  button_html:['<button class="jspsych-html-btn"><img src="../static/images/task_images/aliens/old_aliens/icon/alien-02.jpg" height="50"></button>','<button class="jspsych-html-btn"><img src="../static/images/task_images/aliens/old_aliens/icon/alien-03.jpg" height="50"></button>','<button class="jspsych-html-btn"><img src="../static/images/task_images/aliens/old_aliens/icon/alien-04.jpg" height="50"></button>'],
  margin_horizontal: '300px',

}



//timeline.push(welcome)
//timeline.push(decision)
//timeline.push(dig)
timeline.push(compare_alien)


jsPsych.init({
  timeline: timeline,
  max_load_time: 60000,
  use_webaudio: false,
  on_finish: function() {
    jsPsych.data.displayData('csv')
  }
})
