/*
 * Requires:
 *     psiturk.js
 *     utils.js
 */

/********************
* HTML manipulation
*
* All HTML files in the templates directory are requested
* from the server when the PsiTurk object is created above. We
* need code to get those pages from the PsiTurk object and
* insert them into the document.
*
********************/
var debug_mode = 0; // debug mode determines how long the blocks are, 5 sec in debug mode, 5 minutes in actual experiment
//var data_save_method = 'csv_server_py';
var data_save_method = 'csv_server_py';

/* Disable right-click/context menu */
if(debug_mode == false) {
  document.addEventListener('contextmenu', function (event) { event.preventDefault(); });
}

/* Escape key or exit fullscreen ends experiment */

// Callback function for handling potential end-experiment-triggering events
function exit_handler(event) {
  var exit_message = "The experiment was ended by pressing the escape key or exiting fullscreen.";
  // If 'esc' key pressed or exiting fullscreen (but not if experiment-triggered exit)
  if(event.code == 'Escape' || (event.type == 'fullscreenchange' && !document.webkitIsFullScreen &&
      !document.mozFullScreen && !document.msFullscreenElement) && normal_exit == false) {
    jsPsych.endExperiment(exit_message);
  }
}

// BETA DIST //
function sum(nums) {
  var accumulator = 0;
  for (var i = 0, l = nums.length; i < l; i++)
    accumulator += nums[i];
  return accumulator;
}


function rbeta(alpha, beta) {
  var alpha_gamma = rgamma(alpha, 1);
  return alpha_gamma / (alpha_gamma + rgamma(beta, 1));
}

// From Python source, so I guess it's PSF Licensed
var SG_MAGICCONST = 1 + Math.log(4.5);
var LOG4 = Math.log(4.0);

function rgamma(alpha, beta) {
  // does not check that alpha > 0 && beta > 0
  if (alpha > 1) {
    // Uses R.C.H. Cheng, "The generation of Gamma variables with non-integral
    // shape parameters", Applied Statistics, (1977), 26, No. 1, p71-74
    var ainv = Math.sqrt(2.0 * alpha - 1.0);
    var bbb = alpha - LOG4;
    var ccc = alpha + ainv;

    while (true) {
      var u1 = Math.random();
      if (!((1e-7 < u1) && (u1 < 0.9999999))) {
        continue;
      }
      var u2 = 1.0 - Math.random();
      v = Math.log(u1/(1.0-u1))/ainv;
      x = alpha*Math.exp(v);
      var z = u1*u1*u2;
      var r = bbb+ccc*v-x;
      if (r + SG_MAGICCONST - 4.5*z >= 0.0 || r >= Math.log(z)) {
        return x * beta;
      }
    }
  }
  else if (alpha == 1.0) {
    var u = Math.random();
    while (u <= 1e-7) {
      u = Math.random();
    }
    return -Math.log(u) * beta;
  }
  else { // 0 < alpha < 1
    // Uses ALGORITHM GS of Statistical Computing - Kennedy & Gentle
    while (true) {
      var u3 = Math.random();
      var b = (Math.E + alpha)/Math.E;
      var p = b*u3;
      if (p <= 1.0) {
        x = Math.pow(p, (1.0/alpha));
      }
      else {
        x = -Math.log((b-p)/alpha);
      }
      var u4 = Math.random();
      if (p > 1.0) {
        if (u4 <= Math.pow(x, (alpha - 1.0))) {
          break;
        }
      }
      else if (u4 <= Math.exp(-x)) {
        break;
      }
    }
  }
}


  function testbeta(a, b, N) {
    var sample_mean = sum(_.range(N).map(function() { return rbeta(a, b); })) / N;
    var analytic_mean = a / (a + b);
    console.log(sample_mean, "~", analytic_mean);
  }

  function get_decay_rate(galaxy) {
    if (galaxy == 0) {
      var decay_rate = rbeta(13, 51);
    } else if (galaxy == 1) {
      var decay_rate = rbeta(50, 50);
    } else if (galaxy == 2) {
      var decay_rate = rbeta(50, 12);
    }
    return decay_rate;
  }


////////// PAVLOVIA ////////////
// var pavlovia_init = {
// 	type: "pavlovia",
// 	command: "init"
// };

// var pavlovia_finish = {
// 	type: "pavlovia",
// 	command: "finish"
// 	};
///////////////////////////////

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

// Yates-Fischer algorithm
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

// for getting a list of random numbers 0 to 42
function rand_list(upper_bound) {
  var arr = Array.from(Array(upper_bound).keys())
  arr = arr.map(function(val){return ++val;});
  shuffle(arr);
  return arr
}

// for free-sort
var get_icons = function (aliens, old_aliens, new_aliens) {
  arr = []
  for (let i = 0; i < aliens.length; i++) {
    arr.push(old_aliens[aliens[i]-1]);
  }

  for (let i = 0; i < new_aliens.length; i++) {
    arr.push(new_aliens[i]);
  }
  return arr;
}


//////////// QUIZ CHECK ?////////////////////////

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

var q_missed = 0;
var num_quiz_failures = 0;
// for quiz
var correct_answers = ['C','B','B','A','B'];

///////////////////////////////////////////////

// Will be set to true when experiment is exiting fullscreen normally, to prevent above end experiment code
var normal_exit = false;
var window_height = window.screen.height;


// FROM QUALTRICS
var participant_id = jsPsych.data.getURLVariable('participant_ID');
var subject_id = jsPsych.data.getURLVariable('subject_ID');
var age = jsPsych.data.getURLVariable('age');
var gender = jsPsych.data.getURLVariable('gender');
var cond = 1;

//////////////////////////////////////////////////////////////

var timeline = []; // structures the experiment
// timeline.push(pavlovia_init);

//////////////IMAGES ///////////////////////////
function parse(str) {
  console.log('parse')
    var args = [].slice.call(arguments, 1),
        i = 0;

    return str.replace(/%s/g, () => args[i++]);
}

var main_stim_string = "<img src='../static/images/task_images/aliens/old_aliens/icon/alien-%s.jpg'>"

var button_string ='<button class="jspsych-html-btn"><img src="../static/images/task_images/aliens/old_aliens/icon/alien-%s.jpg" height="50"></button>'



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

//////////////////////////////////////////////////////////////

///////////////INITIALIZE IMPORTANT VARS ////////////////////
// when to end block timing
var block_start;
var b_num = 1;

if (debug_mode) {
  var total_num_blocks =0;
	var block_len = 20000;
  var n_prac_trials = 0;
} else {
  //var total_num_blocks = 1;
  var total_num_blocks = 4;
  var block_len = [300000,300000,300000,300000]; // array of how long block_len should be
  //var block_len = [1500,1500,1500,1500];
  var n_prac_trials = 4;
  timeline.push({
    type: 'fullscreen',
    fullscreen_mode: true
  });
}

// number of planets visited and time spent on planet
var planet = 0;
var prt = 0;
var total_space_treasure = 0;
var cents_per_gem = 0.0002; /* 5000 gems you get a dollar */
var planet_left,planet_right,alien_left,alien_right;
var num_planets = []; // keep track of number of planets we visit in each block
var true_planet = [];

var block_num_planet = 0;

// practice trials
var curr_prac_trial = 1;
var n_prac_rounds = 1;

// aliens
var aliens_prac = [1,2,3,4,5];
var aliens = rand_list(80); // will pop every time use a new alien

var aliens_copy = [];
var alien;
var alien_check = [[42,9,2,24],[0,20,4,5],[62,8,40,23],[44,61,80,64],[63,61,2,29],[82,22,45,66],[6,1,43,41],[21,60,28,46],[26,60,3,67]];
//var alien_check = [[0,1,2,3],[20,21,22,23],[40,41,42,43],[60,61,62,63]];
shuffle(alien_check); // shuffle to ensure order is random for every participant
var buttons; // to save latter
/////////////////////////////////////////////////////////////

var drop_trials = function (alien_check,true_planet) {
  var compare_trials = []
  var n_trials = alien_check.length
  for (var i = 0; i < n_trials; i++) {
    var curr_trial = alien_check[i]
    var keep_trial = true;
    for (var j = 0; j< 4; j++) {
      if (!true_planet.includes(curr_trial[j])) {
        var keep_trial= false;
      }
    }
    if (keep_trial) {
      compare_trials.push(1)
    } else {
      compare_trials.push(0)
    }
  }
  return compare_trials
}

//////////////////FOR INSTRUCTIONS///////////////////////////
var go_back = function(data) {
  if (data.trial_type == 'welcome_dec') {
    jsPsych.addNodeToEndOfTimeline({timeline: [welcome,move_explain,welcome_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_goal') {
    jsPsych.addNodeToEndOfTimeline({timeline: [welcome,move_explain,welcome_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_dig') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_goal,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_travel') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_dig,instructions_dig_try,dig_prac,instructions_travel,instructions_travel_try,travel_prac,instructions_alien,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_alien_greet') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_dig,instructions_dig_try,dig_prac,instructions_travel,instructions_travel_try,travel_prac,instructions_alien,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'time_out') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_alien,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);}}

var go_forward = function(data) {
  if (data.trial_type == 'welcome_dec') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_goal,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_goal') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_dig,instructions_dig_try,dig_prac,instructions_travel,instructions_travel_try,travel_prac,instructions_alien,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_dig') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_travel,instructions_travel_try,,travel_prac,instructions_alien,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_travel') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_alien,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_alien_greet') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_time_out,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'time_out') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_break,instruc_dec,lock_choice],}, jsPsych.resumeExperiment);
  } else if (data.trial_type == 'instruc_break') {
    jsPsych.addNodeToEndOfTimeline({timeline: [instructions_practice_game, begin_practice],}, jsPsych.resumeExperiment);
  }}

//////////////////////////////////////////////////////////////////




/* STRUCTURE OF GAME - TYPES OF TRIALS */
// arival at new planet
var landing = {
	type: 'image-keyboard-response',
	stimulus: land_img,
  prompt: "<p style = 'color:white;'>Dig here or travel to a new planet?</p>",
	stimulus_height: 700,
	choices: jsPsych.NO_KEYS,
	stimulus_duration: 500,
	trial_duration: 500,
	on_finish: function(data) {
		data.next_reward = Math.round(Math.max(Math.min(normalRandomScaled(100,5),135),0));
		data.planet = planet;
		data.trial_type = "land";
	}
}

var landing_prac = {
	type: 'image-keyboard-response',
	stimulus: land_img,
  prompt: "<p style = 'color:white;'><strong>Practice Trial</strong></p> <p style = 'color:white;'>Dig here ('Q') or travel to a new planet ('P')?</p>",
	stimulus_height: 700,
	choices: jsPsych.NO_KEYS,
	stimulus_duration: 500,
	trial_duration: 500,
	on_finish: function(data) {
		data.next_reward = Math.round(Math.max(Math.min(normalRandomScaled(100,5),135),0));
		data.planet = planet;
		data.trial_type = "land_prac";
	}
}

// digging digging
var dig = {
	type: 'animation',
	stimuli: dig_sequence,
  prompt: "<p style = 'color:white;font-size:22px;'> Dig here or travel to a new planet?</p>",
  frame_time: 667,
  choices: jsPsych.NO_KEYS,
  on_start: function(dig) {
    var last_trial_data = jsPsych.data.get().last(1).values()[0];
    if (last_trial_data.trial_type == "decision") {
      var adjusted_rt = 3000 - last_trial_data.rt;
      dig.frame_time = adjusted_rt/3;
      var src = "../static/audio/axe.mp3#t=2.0,"
      var tt_sec = Math.max(adjusted_rt/1000-1.5,1); //need to convert to seconds
      var axe_audio = new sound(src.concat(tt_sec.toString()))
      axe_audio.play()
    } else {
      var src = "../static/audio/axe.mp3#t=2.0,"
      var tt_sec = 1.0; //need to convert to seconds
      var axe_audio = new sound(src.concat(tt_sec.toString()))
      axe_audio.play()
    }
  },
	on_finish: function(data) {
		var last_trial_data = jsPsych.data.get().last(1).values()[0];
		data.next_reward = last_trial_data.next_reward;
		data.planet = planet;
		data.trial_type = "dig";
	}
};

var dig_instruc = {
  type: 'animation',
  stimuli: dig_sequence,
  prompt: "<p style = 'color:white;font-size:21px;'> Dig here or travel to a new planet?</p>",
  choices: jsPsych.NO_KEYS,
  frame_time: 667,
  on_start: function(dig_instruc) {
    var src = "../static/audio/axe.mp3#t=2.0,"
    var tt_sec = 1.0; //need to convert to seconds
    var axe_audio = new sound(src.concat(tt_sec.toString()))
    axe_audio.play()
  },
	on_finish: function(data) {
		data.trial_type = "dig_instruc";
	}
}

var dig_prac = {
  type: 'animation',
  stimuli: dig_sequence,
  prompt: "<p style = 'color:white;font-size:21px;'><strong>Practice Trial</strong></p> <p style = 'color:white;'>Dig here ('Q') or travel to a new planet ('P')?</p>",
  choices: jsPsych.NO_KEYS,
  frame_time: 667,
  on_start: function(dig_prac) {
    var last_trial_data = jsPsych.data.get().last(1).values()[0];
    if (last_trial_data.trial_type == "decision") {
      var adjusted_rt = 3000 - last_trial_data.rt;
      dig_prac.frame_time = adjusted_rt/3;
      var src = "../static/audio/axe.mp3#t=2.0,"
      var tt_sec = Math.max(adjusted_rt/1000-1.5,1); //need to convert to seconds
      var axe_audio = new sound(src.concat(tt_sec.toString()))
      axe_audio.play()
    } else {
      var src = "../static/audio/axe.mp3#t=2.0,"
      var tt_sec = 1.0; //need to convert to seconds
      var axe_audio = new sound(src.concat(tt_sec.toString()))
      axe_audio.play()
    }
  },
	on_finish: function(data) {
		data.trial_type = "dig_prac";
	}
}

// digging up the treasure, displaying how many gems they got
var harvest = {
	type: 'image-keyboard-response',
	stimulus: space_treasure_img,
  prompt: "<p style ='color:white;'>Dig here or travel to a new planet?</p>",
	stimulus_height:700,
	stimulus_duration: 1000, // in milliseconds
	trial_duration: 1000,
	choices: jsPsych.NO_KEYS,
	on_start: function(harvest) {
		var last_trial_data = jsPsych.data.get().last(2).values()[0]; // last trial was dig, before that was decision
		var reward = last_trial_data.next_reward; // round to one decimal point
		var folder_prefix = '../static/images/task_images/gems/';
		var integer = Math.round(reward.toString());
		var img_suffix = '.jpg'
		var harvest_img = folder_prefix.concat(integer,img_suffix)
		harvest.stimulus = harvest_img;
	},
	on_finish: function(data) {
    var last_trial_data = jsPsych.data.get().last(3).values()[0];
    var galaxy_type = struc[b_num-1][block_num_planet-1]
		var decay_rate = get_decay_rate(galaxy_type);
    data.reward_received = last_trial_data.next_reward; // what did we receive from this harvest
		data.next_reward = Math.round(last_trial_data.next_reward*decay_rate);
		data.decay_rate_actual = decay_rate;
		data.decay_rate_exp = data.next_reward/last_trial_data.next_reward; // calculate the decay rate as seen by the  participant not what was actual sampled
    data.planet = planet;
		data.trial_type = "harvest";
    window.total_space_treasure = total_space_treasure + last_trial_data.next_reward;

	},
};

// display barrels of gems instead of actual gems
var harvest_prac = {
	type: 'image-keyboard-response',
  prompt: "<p style = 'color:white;'><strong>Practice Trial</strong></p> <p style = 'color:white;'>Dig here ('Q') or travel to a new planet ('P')?</p>",
	stimulus: harvest_practice_img,
	stimulus_height:700,
	stimulus_duration: 1000, // in milliseconds
	trial_duration: 1000,
	choices: jsPsych.NO_KEYS,
  on_finish: function(data) {
		data.trial_type = "harvest_prac";
	}
}

var harvest_instruc = {
	type: 'image-keyboard-response',
	stimulus: '../static/images/task_images/gems/100.jpg',
  prompt: "<p style ='color:white;'>Dig here or travel to a new planet?</p>",
	stimulus_height:700,
	stimulus_duration: 1000, // in milliseconds
	trial_duration: 1000,
	choices: jsPsych.NO_KEYS,
	on_finish: function(data) {
		data.trial_type = "harvest_instruc";
  }
};


 var travel = {
	 type: 'animation',
	 stimuli: travel_sequence,
   prompt: "<p style ='color:white;'>Dig here or travel to a new planet?</p>",
	 frame_time: 1111, // in milliseconds
	 choices: jsPsych.NO_KEYS,
   on_start: function(travel) {
     var last_trial_data = jsPsych.data.get().last(1).values()[0];
     var last_rt = last_trial_data.rt;
     var adjusted_travel_time = 10000 - last_rt;
     travel.frame_time = adjusted_travel_time/9;
     var src = "../static/audio/rocket.mp3#t=0,"
     var tt_sec = adjusted_travel_time/1000-0.5; //need to convert to seconds
     var rocket_audio = new sound(src.concat(tt_sec.toString()))
     rocket_audio.play()
   },
   on_finish: function(data) {
     data.trial_type = "travel";
     data.planet = planet;
   }
 };

 var travel_prac = {
   type: 'animation',
   stimuli: travel_sequence,
   prompt: "<p style = 'color:white;'><strong>Practice Trial</strong></p> <p style = 'color:white;'>Dig here ('Q') or travel to a new planet ('P')?</p>",
   frame_time: 1111, // in milliseconds
   choices: jsPsych.NO_KEYS,
   on_start: function() {
     var last_trial_data = jsPsych.data.get().last(1).values()[0];
     var last_rt = last_trial_data.rt;
     var adjusted_travel_time = 10000 - last_rt;
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


 var decision = {
	 type: 'image-keyboard-response',
	 stimulus: decision_img,
	 stimulus_height:700,
   trial_duration:3000,
	 prompt:"<p>Dig here or travel to a new planet?<p>",
   choices: ['A', 'L'],
	 on_finish: function(data) {
		var last_trial_data = jsPsych.data.get().last(2).values()[0];
    var last_two_trial_data = jsPsych.data.get().last(8).values()[0];

		data.next_reward = last_trial_data.next_reward;
		data.time_in_block = Date.now() - block_start;
		data.block_num = b_num;
		data.planet = planet;
		data.prt = prt;
    data.trial_type = "decision";


		 // end of block/ experiment
  if ((data.time_in_block >= block_len[b_num-1]) | (block_num_planet == 20))  {
       num_planets.push(planet)

         // if this is the last block
       if (b_num == total_num_blocks) { // end of block or end of exp
          const reducer = (accumulator, currentValue) => accumulator + currentValue;

          var compare_trials = drop_trials(alien_check,true_planet)
          if (compare_trials.reduce(reducer) > 0) {
            jsPsych.addNodeToEndOfTimeline({timeline: [instructions_compare_read,instructions_compare_continue],}, jsPsych.resumeExperiment);


          if (compare_trials[0] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_0],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[1] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_1],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[2] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_2],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[3] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_3],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[4] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_4],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[5] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_5],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[6] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_6],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[7] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_7],}, jsPsych.resumeExperiment);
          }
          if (compare_trials[8] == 1) {
            jsPsych.addNodeToEndOfTimeline({timeline: [compare_alien_8],}, jsPsych.resumeExperiment);
          }}

          jsPsych.addNodeToEndOfTimeline({timeline: [end_of_experiment_read],}, jsPsych.resumeExperiment);

         // other blocks
         } else { // if this is the firs =t or second and choose to leave
          jsPsych.addNodeToEndOfTimeline({timeline: [end_of_block_read],}, jsPsych.resumeExperiment);
         }

         window.prt = 0;
         window.block_num_planet = 0;
         data.last_trial_on_planet = true;
         window.b_num = b_num + 1;
     // not the end
    } else {
      // travel
      if (data.key_press == jsPsych.pluginAPI.convertKeyCharacterToKeyCode('L'))  {

        jsPsych.addNodeToEndOfTimeline({timeline: [travel,alien_welcome,landing,dig,harvest,decision]}, jsPsych.resumeExperiment);
        data.last_trial_on_planet = true;
        window.prt = 0;

    // stay
    } else if (data.key_press == jsPsych.pluginAPI.convertKeyCharacterToKeyCode('A'))  {
      jsPsych.addNodeToEndOfTimeline({
         timeline: [dig,harvest,decision],
       }, jsPsych.resumeExperiment);

     window.prt = prt + 1;
     data.last_trial_on_planet = false;

      if ((last_two_trial_data.next_reward == last_trial_data.next_reward) & last_trial_data.next_reward < 5) {
            data.next_reward = 0}
    // didn't make choice
    } else {
      jsPsych.addNodeToEndOfTimeline({
        timeline: [time_out,decision],
      }, jsPsych.resumeExperiment);
      data.last_trial_on_planet = false;}
    }
  }}


var decision_prac = {
  type: 'image-keyboard-response',
  stimulus: decision_img,
  stimulus_height:700,
  trial_duration:3000,
  choices: ['A', 'L'],
  prompt: "<p><strong>Practice Trial</strong></p> <p>Dig here ('A') or travel to a new planet ('L')?</p>",
  on_finish: function(data) {
    data.trial_type = "decision_prac";
    if (curr_prac_trial > n_prac_trials) {
      jsPsych.addNodeToEndOfTimeline({
        timeline: [quiz_instruc,instructions_repeat,instructions_repeat_continue,quiz_q_1_ask],
      }, jsPsych.resumeExperiment);
      data.n_prac_rounds = n_prac_rounds
    } else {
      if (data.key_press == jsPsych.pluginAPI.convertKeyCharacterToKeyCode('A')) {
        // they chose to arvest
        jsPsych.addNodeToEndOfTimeline({
          timeline: [dig_prac,harvest_prac,decision_prac],
        }, jsPsych.resumeExperiment);
      } else if (data.key_press == jsPsych.pluginAPI.convertKeyCharacterToKeyCode('L')) {
        jsPsych.addNodeToEndOfTimeline({
          timeline: [travel,alien_welcome_prac,landing_prac,dig_prac,harvest_prac,decision_prac],
        }, jsPsych.resumeExperiment);
      } else {
        jsPsych.addNodeToEndOfTimeline({
          timeline: [time_out,decision_prac],
        }, jsPsych.resumeExperiment);
      }
      last_trial_data = jsPsych.data.get().last(1).values()[0];
      data.next_reward = last_trial_data.next_reward;
      data.curr_prac_trial = curr_prac_trial;
      window.curr_prac_trial = curr_prac_trial + 1;}}};

var time_out = {
  type: 'image-keyboard-response',
  stimulus: time_out_img,
  prompt: "<p style = 'color:white;'>Dig here or travel to a new planet?</p>",
  stimulus_height:700,
  stimulus_duration: 2000, // in milliseconds
  trial_duration: 2000,
  choices: jsPsych.NO_KEYS,
  on_finish: function(data) {
    data.trial_type = "time_out";
    var last_trial_data = jsPsych.data.get().last(2).values()[0];
    var last_trial_data =
    data.next_reward = last_trial_data.next_reward;
    console.log(last_trial_data)}
  }

var quiz_instruc = {
  type:'audio-button-response',
  stimulus: "../static/audio/clip_10_quiz.m4a",
  prompt: practice_game_finish_txt,
  choices: ['continue'],
  on_finish: function(data) {
    data.trial_type = "quiz_instruc";}
  }

var quiz_q_1_ask = {
  type:'audio-button-response',
  stimulus: "../static/audio/clip_11_q1_ask.m4a",
  prompt: "<p>How do you win extra money?</p>",
  choices: ['Visiting more planets','Staying at home base longer', 'Collecting more gems'],
  on_finish: function(data) {
    data.trial_type = "quiz_q_1_ask";
    if (data.button_pressed == '2') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_1_fb_correct,quiz_q_2_ask],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_1_fb_incorrect,quiz_q_2_ask],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;}}
 }

var quiz_q_1_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_12_q1_correct.m4a",
  prompt: "<p>That’s correct. You win extra money by collecting more gems.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    console.log('fb')
    data.prompt = "<p>That’s correct. You win extra money by collecting more gems.</p>";
    data.trial_type = "quiz_q_1_fb_correct";}
  }

var quiz_q_1_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_13_q1_incorrect.m4a",
  prompt: "<p>That’s incorrect. You win extra money by collecting more gems.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.prompt = "<p>That’s incorrect. You win extra money by collecting more gems.</p>";
    data.trial_type = "quiz_q_1_fb_incorrect";}
  }

var quiz_q_2_ask = {
  type:'audio-button-response',
  stimulus: "../static/audio/clip_14_q2_ask.m4a",
  prompt: "<p>The length of this experiment</p>",
  choices: ["Depends on how many planets you've visited","is 20 minutes no matter what","depends on how many gems you've collected"],
  on_finish: function(data) {
    data.trial_type = "quiz_q_2_ask";
    if (data.button_pressed == '1') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_2_fb_correct,quiz_q_3_ask],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_2_fb_incorrect,quiz_q_3_ask],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;}}
  };


var quiz_q_2_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_15_q2_correct.m4a",
  prompt: "<p>That’s correct. The experiment is 20 minutes no matter what.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_2_fb_correct";
    data.prompt = "<p>That’s correct. The experiment is 20 minutes no matter what.</p>";}
  }

var quiz_q_2_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_16_q2_incorrect.m4a",
  prompt: "<p>That’s incorrect. The experiment is 20 minutes no matter what.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_2_fb_incorrect";
    data.prompt = "<p>That’s incorrect. The experiment is 20 minutes no matter what.</p>";}
  }

var quiz_q_3_ask = {
  type:'audio-button-response',
  stimulus: "../static/audio/clip_17_q3_ask.m4a",
  prompt: "<p>You press what letter on your keyboard to travel to a new planet?</p>",
  choices: ['A','L'],
  on_finish: function(data) {
    data.trial_type = "quiz_q_3_ask";
    if (data.button_pressed == '1') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_3_fb_correct,quiz_q_4_ask],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_3_fb_incorrect,quiz_q_4_ask],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;}}
  }


var quiz_q_3_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_18_q3_correct.m4a",
  prompt: "<p> That’s correct. You press the letter L to travel to a new planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_3_fb_correct";
    data.prompt = "<p> That’s correct. You press the letter L to travel to a new planet.</p>";}
  };

var quiz_q_3_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_19_q3_incorrect.m4a",
  prompt: "<p>That’s incorrect.  You press the letter L to travel to a new planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_3_fb_incorrect";
    data.prompt = "<p>That’s incorrect.  You press the letter L to travel to a new planet.</p>";}
  };


var quiz_q_4_ask = {
  type:'audio-button-response',
  stimulus: "../static/audio/clip_20_q4_ask.m4a",
  prompt: "<p>The more you dig on a planet the fewer gems you’ll get with each dig.</p>",
  choices: ['True','False'],
  on_finish: function(data) {
    data.trial_type = "quiz_q_4_ask";
    if (data.button_pressed == '0') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_4_fb_correct,quiz_q_5_ask],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_4_fb_incorrect,quiz_q_5_ask],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;}}
  }


var quiz_q_4_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_21_q4_correct.m4a",
  prompt: "<p> That’s correct. The more you dig on a planet the fewer gems you’ll get with each dig. </p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_4_fb_correct";
    data.prompt = "<p> That’s correct. The more you dig on a planet the fewer gems you’ll get with each dig. </p>";}
  };

var quiz_q_4_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_22_q4_incorrect.m4a",
  prompt: "<p>That’s incorrect.  The more you dig on a planet the fewer gems you’ll get with each dig.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_4_fb_incorrect";
    data.prompt = "<p>That’s incorrect.  The more you dig on a planet the fewer gems you’ll get with each dig.</p>";}
  };

var quiz_q_5_ask = {
  type:'audio-button-response',
  stimulus: "../static/audio/clip_23_q5_ask.m4a",
  prompt: "<p>Does the alien tell you anything about how much treasure is on the planet?</p>",
  choices: ['Yes','No'],
  on_finish: function(data) {
    data.trial_type = "quiz_q_5_ask";
    if (data.button_pressed == '1') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_5_fb_correct],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_5_fb_incorrect],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;}
      if (q_missed > 0) {
        console.log(num_quiz_failures)
        if (num_quiz_failures < 2) {
          jsPsych.addNodeToEndOfTimeline({timeline: [quiz_incorrect,quiz_incorrect_continue,quiz_q_1_ask],}, jsPsych.resumeExperiment);
          window.num_quiz_failures= num_quiz_failures + 1;
        } else {
          jsPsych.addNodeToEndOfTimeline({timeline: [quiz_correct,quiz_correct_continue,instructions_begin_exp,instructions_begin_exp_continue],}, jsPsych.resumeExperiment);}
      } else {
        jsPsych.addNodeToEndOfTimeline({timeline: [quiz_correct,quiz_correct_continue,instructions_begin_exp,instructions_begin_exp_continue],}, jsPsych.resumeExperiment);}
      window.q_missed = 0;}
  };


var quiz_q_5_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_24_q5_correct.m4a",
  prompt: "<p> That’s correct. The alien tells you nothing about how much treasure is on the planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_5_fb_correct";
    data.prompt = "<p> That’s correct. The alien tells you nothing about how much treasure is on the planet.</p>";}
  };

var quiz_q_5_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_25_q5_incorrect.m4a",
  prompt: "<p>That’s incorrect. The alien tells you nothing about how much treasure is on the planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_5_fb_incorrect";
    data.prompt = "<p>That’s incorrect. The alien tells you nothing about how much treasure is on the planet.</p>";}
  };

var quiz_correct = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_26_correct_quiz.m4a",
  prompt: quiz_correct_txt,
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_correct";}
  }


var quiz_correct_continue = {
  type:'html-button-response',
  stimulus:quiz_correct_txt,
  choices:['continue'],
  on_finish: function(data) {
      data.trial_type = 'quiz_correct_continue';}
  }

var quiz_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "../static/audio/clip_27_incorrect_quiz.m4a",
  prompt: quiz_incorrect_txt,
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_incorrect";}}


var quiz_incorrect_continue = {
  type:'html-button-response',
  stimulus:quiz_incorrect_txt,
  choices: ['re-take the quiz'],
  on_finish: function(data) {
    data.trial_type = 'quiz_incorrect_continue';
    window.num_quiz_failures= num_quiz_failures + 1;}
 }


var alien_welcome = {
  type: 'image-keyboard-response',
  prompt: "<p style ='color:white;'>Dig here or travel to a new planet?</p>",
  stimulus: time_out_img,
  stimulus_height:700,
  stimulus_duration: 5000, // in milliseconds
  trial_duration: 5000,
  choices: jsPsych.NO_KEYS,
  on_start: function(alien_welcome) {
    window.alien = aliens.pop().toString();
    console.log('alien')
    console.log(alien)
    window.aliens_copy.push(alien)
    console.log('aliens_copy')
    console.log(aliens_copy)
    alien_welcome.stimulus = "../static/images/task_images/aliens/old_aliens/planet/alien_planet-".concat(alien,'.jpg')
  },
  on_finish: function(data) {
  	window.planet = planet + 1;
  	window.block_num_planet = block_num_planet + 1;
    data.alien = alien;
    data.aliens = aliens_copy; // save the list of aliens here
    true_planet.push((block_num_planet + (b_num-1)*20)-1)
    data.trial_type = "alien_welcome";
  }
}

var alien_welcome_prac = {
  type: 'image-keyboard-response',
  stimulus: time_out_img,
  prompt: "<p style = 'color:white;'><strong>Practice Trial</strong></p> <p style = 'color:white;'>Dig here ('Q') or travel to a new planet ('P')?</p>",
  stimulus_height:700,
  stimulus_duration: 5000, // in milliseconds
  trial_duration: 5000,
  choices: jsPsych.NO_KEYS,
  on_start: function(alien_welcome_prac) {
    window.alien = aliens_prac.pop().toString();
    alien_welcome_prac.stimulus = "../static/images/task_images/aliens/practice_aliens/planet/alien_planet-".concat(alien,'.jpg')
  },
  on_finish: function(data) {
    data.trial_type = "alien_welcome_prac";
  }
}

var sort_trial = {
    type: 'free-sort',
    stimuli: old_aliens,
    prompt: "<p>Click and drag the images below to sort them so that similar items are close together.</p>",
    sort_area_shape: "square",
    scale_factor:1.5,
    sort_area_width:1000,
    border_width:5,
    change_border_background_color: false,
    on_start: function(sort_trial) {
      sort_images = get_icons(aliens_copy, old_aliens, new_aliens)
      sort_trial.stimuli = sort_images;
    }
};

 /* INSTRUCTIONS   */

 // Welcome
 var welcome = {
   type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_1_welcome.m4a',
   prompt: welcome_txt,
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true,
   on_finish: function(data) {
     data.trial_type = "instruc_welcome";
     data.prompt = welcome_txt;
     data.subject_id = subject_id;
     data.participant_id = participant_id;
     data.age = age;
     data.gender = gender;

   }
 };

 var move_explain= {
   type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_2_move.m4a',
   prompt: move_explain_txt,
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true,
 };

 var welcome_dec = {
   type: 'html-button-response',
   stimulus: welcome_txt,
   prompt:'Click on the blue planet to re-read the instructions on the last page. Click the green planet to move on to more instructions.',
   choices:['backward','forward'],
   button_html:[move_button_1,move_button_2],
   margin_horizontal: '100px',
   on_finish: function(data) {
     last_last_trial = jsPsych.data.get().last(2).values()[0];

     data.trial_type = 'welcome_dec';
   }};

 var instructions_goal = {
   type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_3_goal.m4a',
   prompt: goal_txt,
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true,
   on_finish: function(data) {
     data.trial_type = "instruc_goal";
     data.prompt = goal_txt;

   }
 };

 var instructions_dig = {
   type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_4_dig.m4a',
   prompt: dig_txt,
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true,
   on_finish: function(data) {
    data.next_reward = 100.0;
    data.trial_type = "instruc_dig"
  }
 };

 var instructions_dig_try = {
   type: 'html-keyboard-response',
   stimulus: dig_txt,
   choices: ['A'],
   on_finish: function(data) {
    data.next_reward = 100.0;
    data.trial_type = "instruc_dig_try";
    data.prompt = data.stimulus;}
 };


 var instructions_travel = {
   type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_5_travel.m4a',
   prompt: travel_txt,
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true,
   on_finish: function(data) {
     data.trial_type = "instruc_travel";
     data.prompt = travel_txt;
   }
 };

 var instructions_travel_try = {
   type: 'html-keyboard-response',
   stimulus: travel_txt,
   choices: ['L'],
   response_ends_trial: true,
   on_finish: function(data) {
     data.trial_type = "instruc_travel_try";
     data.prompt = travel_txt;
   }
 };

 var instructions_alien = {
   type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_6_alien.m4a',
   prompt: alien_txt,
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true,
   on_finish: function(data) {
     data.trial_type = "instruc_alien_greet";
     data.prompt =alien_txt
   }
 }

 var instructions_time_out = {
   type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_7_timeout.m4a',
   prompt: time_out_txt,
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true,
   on_finish: function(data) {
     data.trial_type = "time_out";
     data.prompt = time_out_txt; // used to be 400 height
   }
 }

 var instructions_break = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/clip_8_break.m4a',
 	prompt:  break_txt,
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
   on_finish: function(data) {
     data.trial_type = "instruc_break";
     data.prompt=  break_txt;
   }};

var instructions_practice_game = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/clip_9_practice.m4a',
 	prompt: practice_game_txt,
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
     data.trial_type = "instruc_prac_game";
     data.prompt=practice_game_txt;
   }};

var instructions_repeat = {
    type: 'audio-keyboard-response',
    stimulus:'../static/audio/clip_29_instruct_again.m4a',
   	prompt: instructions_repeat_txt,
    choices: jsPsych.NO_KEYS,
    trial_ends_after_audio: true,
    on_finish: function(data) {
       data.trial_type = "instruc_repeat";
       data.prompt = instructions_repeat_txt;
       data.stimulus = "<p> Are you ready to play a practice game? </p> <p>In this practice game, you'll be digging up barrels of gems. But, in the real game, you'll be digging up the gems themselves. </p>";
     }};

var instructions_repeat_continue = {
  type:'html-button-response',
  stimulus: instructions_repeat_txt,
  choices: ['continue'],
  on_finish: function(data) {
    data.trial_type = "instruc_repeat_continue";
    data.stimulus = "<p> Are you ready to play a practice game? </p> <p>In this practice game, you'll be digging up barrels of gems. But, in the real game, you'll be digging up the gems themselves. </p>";
  }};

 var instruc_dec = {
   type:'html-button-response',
   stimulus: "<p>hello</p>",
   prompt:'Click on the blue planet to re-read the instructions on the last page. Click the green planet to move on to more instructions. ',
   choices:['backward','forward'],
   button_html:[move_button_1, move_button_2],
   margin_horizontal: '100px',
   on_start: function (instruc_dec) {
     last_trial = jsPsych.data.get().last(1).values()[0];
     instruc_dec.stimulus = last_trial.prompt;
   },
   on_finish: function(data) {
     last_last_trial = jsPsych.data.get().last(2).values()[0];

     data.trial_type = last_last_trial.trial_type
   }};

 var lock_choice = {
   type:'html-keyboard-response',
   stimulus: '../static/images/task_images/aliens/instructions_aliens/planet/alien_planet-1.jpg',
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
      last_last_trial = jsPsych.data.get().last(2).values()[0];
      if (last_last_trial.button_pressed == 0) {
        go_back(last_last_trial);
      } else {
        go_forward(last_last_trial);}
     }
   };

 var begin_practice= {
 type:'html-button-response',
 stimulus: "<p> Are you ready to play a practice game? </p> <p>In this practice game, you'll be digging up barrels of gems. But, in the real game, you'll be digging up the gems themselves. </p>",
 choices:['play the practice game'],
 on_finish: function(data) {
     jsPsych.addNodeToEndOfTimeline({
        timeline: [alien_welcome_prac,landing_prac,dig_prac,harvest_prac,decision_prac],
      }, jsPsych.resumeExperiment);
   }
 };

 var instructions_begin_exp = {
 	 type: 'audio-keyboard-response',
   stimulus:'../static/audio/clip_28_real_game.m4a',
 	 prompt:'<p>Now that you know how  to dig for space treasure and travel to new planets, you can start exploring! </p><p>Do you want to go over the instructions again or get started with the real game?</p>',
   choices: jsPsych.NO_KEYS,
   trial_ends_after_audio: true};

var instructions_begin_exp_continue = {
  type:'html-button-response',
  stimulus:'<p>Now that you know how  to dig for space treasure and travel to new planets,you can start exploring! </p><p>Do you want to go over the instructions again or get started with the real game?</p>',
  choices:['re-read instructions','real game'],
  on_finish: function(data){
    data.trial_type = "instructions_begin_exp_continue";
    if (data.button_pressed == '0') {
   			 jsPsych.addNodeToEndOfTimeline({
   					timeline: [instructions_repeat,instructions_repeat_continue,instructions_begin_exp,instructions_begin_exp_continue],
   				}, jsPsych.resumeExperiment);
   	} else {
   			jsPsych.addNodeToEndOfTimeline({
   				 timeline: [alien_welcome,landing,dig,harvest,decision],
   			 }, jsPsych.resumeExperiment);
   		 data.n_prac_rounds = n_prac_rounds;
   		 window.block_start = Date.now();}
    data.trial_type = "instruc_begin_exp_contine";}};

var end_of_block_read = {
	type: 'audio-button-response',
  stimulus: '../static/audio/clip_32_block_end.m4a',
	prompt:"<p> You have been traveling for a while. Time to take a rest at home base! </p> <p> When you are ready to continue, press <strong>continue</strong>. </p><p><img src='../static/images/task_images/home_base.jpg' height='700' width='auto'>",
  choices: ['continue'],
  trial_ends_after_audio: true,
  on_start: function(end_of_block_read) {
    var begin_para = "<p> You have been traveling for a while. Time to take a rest at home base! </p> <p> When you are ready to move on, press the <strong>continue</strong> button below. </p>"
    var img = "<p><img src='../static/images/task_images/home_base.jpg' height='700' width='auto'></p>";
		var block_str = (b_num-1).toString();
		var home_base = "<p style='font-size:25px;'> Home Base Visit # ";
    var para_end = "</p>";
		var str_to_display = begin_para.concat(home_base,block_str,para_end,img);
		end_of_block_read.prompt = str_to_display;
	},
	on_finish: function(data) {
    data.trial_type = "end_of_block_read";
    window.block_space_treasure = 0;
    data.trial_type = "end_of_block_continue";
    jsPsych.addNodeToEndOfTimeline({
      timeline: [alien_welcome,landing,dig,harvest,decision],
    }, jsPsych.resumeExperiment);
    window.block_start = Date.now();
	}
};

var end_of_block_continue = {
	type: 'html-button-response',
	stimulus:"<p> You have been traveling for a while. Time to take a rest at home base! </p> <p> When you are ready to continue, press <strong>continue</strong>. </p><p><img src='../static/images/task_images/home_base.jpg' height='700' width='auto'>",
  choices: ['continue'],
  on_start: function(end_of_block_continue) {
    var begin_para = "<p> You have been traveling for a while. Time to take a rest at home base! </p> <p> When you are ready to move on, press the <strong>continue</strong> button below. </p>"
    var img = "<p><img src='../static/images/task_images/home_base.jpg' height='700' width='auto'></p>";
    var block_str = (b_num-1).toString();
    var home_base = "<p style='font-size:25px;'> Home Base Visit # ";
    var para_end = "</p>";
    var str_to_display = begin_para.concat(home_base,block_str,para_end,img);
    end_of_block_continue.stimulus = str_to_display;
	},
	on_finish: function(data) {
    window.block_space_treasure = 0;
    data.trial_type = "end_of_block_continue";
    jsPsych.addNodeToEndOfTimeline({
      timeline: [alien_welcome,landing,dig,harvest,decision],
    }, jsPsych.resumeExperiment);
    window.block_start = Date.now();
	}
};

var instructions_compare_read = {
  type: 'audio-keyboard-response',
  stimulus:'../static/audio/clip_30_compare.m4a',
  prompt:'<p>Great job collecting treasure! We’re now going to ask you some questions about the aliens you met.</p><p>Some aliens took better care of their mines, and so it was easier to collect treasure from them. </p><p>You’ll be shown one main alien and be asked to pick one alien amongst 3 who was most similar to the main alien based on how well they took care of their mines.</p>',
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true};

var instructions_compare_continue = {
  type: 'html-button-response',
  stimulus:'<p>Great job collecting treasure! We’re now going to ask you some questions about the aliens you met.</p><p>Some aliens took better care of their mines, and so it was easier to collect treasure from them. </p><p>You’ll be shown one main alien and be asked to pick one alien amongst 3 who was most similar to the main alien based on how well they took care of their mines.</p>',
  choices:['continue']};


var compare_alien_0 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[0][0];
    var other_aliens = shuffle(alien_check[0].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;
  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;
    console.log("buttons");
    console.log(buttons);
}};

var compare_alien_1 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[1][0];
    var other_aliens = shuffle(alien_check[1].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;
  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;

}};

var compare_alien_2 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[2][0];
    var other_aliens = shuffle(alien_check[2].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;
  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;

}};

var compare_alien_3 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[3][0];
    var other_aliens = shuffle(alien_check[3].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;
  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;

}};

var compare_alien_4 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[4][0];
    var other_aliens = shuffle(alien_check[4].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;
  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;

}};

var compare_alien_5 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[5][0];
    var other_aliens = shuffle(alien_check[5].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;
  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;

}};


var compare_alien_6 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[6][0];
    var other_aliens = shuffle(alien_check[6].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;
  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;
}};


var compare_alien_7 = {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[7][0];
    var other_aliens = shuffle(alien_check[7].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;

}};


var compare_alien_8= {
  type:'html-button-response',
  stimulus:"hello",
  prompt:"Which of the 3 aliens below is most similar to this alien?",
  choices:["alien_1","alien_2","alien_3"],
  margin_horizontal: '300px',
  on_start: function(compare_alien) {
    console.log('start compare alien')
    var main_alien = alien_check[8][0];
    var other_aliens = shuffle(alien_check[8].slice(1,4))
    compare_alien.stimulus = create_main_stimulus(main_alien,true_planet,aliens_copy);
    window.buttons = create_buttons(other_aliens,true_planet,aliens_copy);
    compare_alien.button_html = buttons;  },
  on_finish: function(data) {
    data.trial_type = 'compare_aliens';
    data.button_html = buttons;

}};

var end_of_experiment_read = {
	type: 'audio-button-response',
  stimulus: '../static/audio/clip_31_end.m4a',
	prompt:'<p> Congrats! You are done with the study!</p><br><br><p><img src="../static/images/task_images/opening_img-01.jpg"</p>',
  choices: ['go to the survey'],
  on_start: function(end_of_experiment_read) {
    var curr_bonus = Math.round(total_space_treasure*cents_per_gem);
    var bonus = Math.round(curr_bonus*10)/10;
    var begin_para = "<p> Congrats! You are done with the game!</p>";
    var begin_bonus = "<p> You made $10 plus $";
    var bonus_str = bonus.toString();
    var end_bonus = " in bonus payment! You will recieve an Amazon giftcard with this amount in the next 3 days. You</p>";
    var end_para = "<p>Press the button below to be redirected to the survey.</p><br><br><p><img src='../static/images/task_images/opening_img-01.jpg' height='600' width='auto'></p>"
    end_of_experiment_read.prompt = begin_para.concat(begin_bonus,bonus_str,end_bonus,end_para);
    window.bonus = bonus;
  },
  on_finish: function(data) {
    data.bonus = bonus;
    var last_trial_data = jsPsych.data.get().last(1).values()[0];
    data.prompt = last_trial_data.prompt;
    data.num_failures = num_quiz_failures
    data.trial_type = "end_of_exp_read";
  }
};

var end_of_experiment_continue = {
	type: 'html-button-response',
	stimulus:'<p> Congrats! You are done with the experiment!</p><br><br><p><img src="../static/images/task_images/opening_img-01.jpg"</p>',
  choices: ['end the game'],
  on_start: function(end_of_experiment_continue) {
    var curr_bonus = Math.round(total_space_treasure*cents_per_gem);
    var bonus = Math.round(curr_bonus*10)/10;
    var begin_para = "<p> Congrats! You are done with the game!</p>";
    var begin_bonus = "<p> You made $10 plus $";
    var bonus_str = bonus.toString();
    var end_bonus = " in bonus payment! You will recieve an Amazon giftcard with this amount in the next 3 days. You just have to answer a few short questions and then you'll ve finished with the study. </p>";
    var end_para = "<p>Press the button below to be redirected to the survey.</p><br><br><p><img src='../static/images/task_images/opening_img-01.jpg' height='600' width='auto'></p>"
    end_of_experiment_continue.stimulus = begin_para.concat(begin_bonus,bonus_str,end_bonus,end_para);
  },
  on_finish: function(data) {
    data.bonus = bonus;
    var last_trial_data = jsPsych.data.get().last(1).values()[0];
    data.prompt = last_trial_data.prompt;
    data.num_failures = num_quiz_failures
    data.trial_type = "end_of_exp_continue";
  }
};

// Welcome to the experiment
timeline.push(welcome); // add variable welcome to end of timeline array
timeline.push(move_explain); // add variable welcome to end of timeline array
timeline.push(welcome_dec); // add variable welcome to end of timeline array
timeline.push(lock_choice); // add variable welcome to end of timeline array

//timeline.push(instructions_begin_exp_continue);

all_audio = ['../static/audio/axe.mp3', '../static/audio/clip_10_quiz.m4a', '../static/audio/clip_11_q1_ask.m4a', '../static/audio/clip_12_q1_correct.m4a', '../static/audio/clip_13_q1_incorrect.m4a', '../static/audio/clip_14_q2_ask.m4a', '../static/audio/clip_15_q2_correct.m4a', '../static/audio/clip_16_q2_incorrect.m4a', '../static/audio/clip_17_q3_ask.m4a', '../static/audio/clip_18_q3_correct.m4a', '../static/audio/clip_19_q3_incorrect.m4a', '../static/audio/clip_1_welcome.m4a', '../static/audio/clip_20_q4_ask.m4a', '../static/audio/clip_21_q4_correct.m4a', '../static/audio/clip_22_q4_incorrect.m4a', '../static/audio/clip_23_q5_ask.m4a', '../static/audio/clip_24_q5_correct.m4a', '../static/audio/clip_25_q5_incorrect.m4a', '../static/audio/clip_26_correct_quiz.m4a', '../static/audio/clip_27_incorrect_quiz.m4a', '../static/audio/clip_28_real_game.m4a', '../static/audio/clip_29_instruct_again.m4a', '../static/audio/clip_2_move.m4a','../static/audio/clip_30_compare.m4a', '../static/audio/clip_31_end.m4a','../static/audio/clip_32_block_end.m4a','../static/audio/clip_3_goal.m4a', '../static/audio/clip_4_dig.m4a', '../static/audio/clip_5_travel.m4a', '../static/audio/clip_6_alien.m4a', '../static/audio/clip_7_timeout.m4a', '../static/audio/clip_8_break.m4a',
'../static/audio/clip_9_practice.m4a', '../static/audio/rocket.mp3']

  jsPsych.init({
    timeline: timeline,
    preload_images: all_images,
    preload_audio:all_audio,
    max_load_time: 60000000,
    use_webaudio: false,
    on_trial_start: function(data) {
    var interaction_data = jsPsych.data.getInteractionData();
    var blur_events = interaction_data.filter({event: 'blur'});
    var focus_events = interaction_data.filter({event: 'focus'});
    var fullscreenenter_events = interaction_data.filter({event: 'fullscreenenter'});
    var fullscreenexit_events = interaction_data.filter({event: 'fullscreenexit'});
    jsPsych.data.get().addToLast({interactions: interaction_data.csv()});
    jsPsych.data.get().addToLast({blur_events: blur_events.csv()});
    jsPsych.data.get().addToLast({focus_events: focus_events.csv()});
    jsPsych.data.get().addToLast({fullscreenenter_events: fullscreenenter_events.csv()});
    jsPsych.data.get().addToLast({fullscreenexit_events: fullscreenexit_events.csv()});},
  on_interaction_data_update: function (data) {
    var interaction_data = jsPsych.data.getInteractionData();
    var blur_events = interaction_data.filter({event: 'blur'});
    var focus_events = interaction_data.filter({event: 'focus'});
    var fullscreenenter_events = interaction_data.filter({event: 'fullscreenenter'});
    var fullscreenexit_events = interaction_data.filter({event: 'fullscreenexit'});
    jsPsych.data.get().addToLast({interactions: interaction_data.csv()});
    jsPsych.data.get().addToLast({blur_events: blur_events.csv()});
    jsPsych.data.get().addToLast({focus_events: focus_events.csv()});
    jsPsych.data.get().addToLast({fullscreenenter_events: fullscreenenter_events.csv()});
    jsPsych.data.get().addToLast({fullscreenexit_events: fullscreenexit_events.csv()});},
  on_close: function (data) {
    var interaction_data = jsPsych.data.getInteractionData();
    var blur_events = interaction_data.filter({event: 'blur'});
    var focus_events = interaction_data.filter({event: 'focus'});
    var fullscreenenter_events = interaction_data.filter({event: 'fullscreenenter'});
    var fullscreenexit_events = interaction_data.filter({event: 'fullscreenexit'});
    jsPsych.data.get().addToLast({interactions: interaction_data.csv()});
    jsPsych.data.get().addToLast({blur_events: blur_events.csv()});
    jsPsych.data.get().addToLast({focus_events: focus_events.csv()});
    jsPsych.data.get().addToLast({fullscreenenter_events: fullscreenenter_events.csv()});
    jsPsych.data.get().addToLast({fullscreenexit_events: fullscreenexit_events.csv()});},
  on_finish: function(data) {
    var interaction_data = jsPsych.data.getInteractionData();
    var blur_events = interaction_data.filter({event: 'blur'});
    var focus_events = interaction_data.filter({event: 'focus'});
    var fullscreenenter_events = interaction_data.filter({event: 'fullscreenenter'});
    var fullscreenexit_events = interaction_data.filter({event: 'fullscreenexit'});
    jsPsych.data.get().addToLast({interactions: interaction_data.csv()});
    jsPsych.data.get().addToLast({blur_events: blur_events.csv()});
    jsPsych.data.get().addToLast({focus_events: focus_events.csv()});
    jsPsych.data.get().addToLast({fullscreenenter_events: fullscreenenter_events.csv()});
    jsPsych.data.get().addToLast({fullscreenexit_events: fullscreenexit_events.csv()});

    // document.body.innerHTML = '<p> <center>Thank you for participating in the second part of the study! Please wait while your data saves. After 10 seconds, you will be redirected to Spark. </center> </p>';
    //   setTimeout(function () {var end_link = "https://spark.hartleylab.org/completed/".concat(subject_id); window.location = end_link;}, 10000)
    document.body.innerHTML = '<p> <center>Thank you for participating in this study! Please wait while your data saves. You will be redirected to a survey to answer a few questions then you will be finished. </center> </p>';
      setTimeout(function () {var end_link = "https://nyu.qualtrics.com/jfe/form/SV_0GLuzqpMFZ5GVfw" + "?participant_ID="+participant_id+"&subject_ID=" +subject_id; window.location = end_link;}, 10000)
  }
})
