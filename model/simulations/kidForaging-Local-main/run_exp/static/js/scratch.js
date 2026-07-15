var quiz_instruc = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_10_quiz.m4a",
  prompt: "<p><strong>Great job on the practice game! Now, I'm gonna ask you some questions to make sure you understand the game.</strong></p><p><strong>But, before we do that, let's review some of the instructions.</strong></p><p>[press the space bar to continue]</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_instruc";}
  }

var quiz_continue = {
  type:'html-keyboard-response',
  stimulus:"<p>hello</p>",
  choices:['space'],
  on_start: function(quiz_continue) {
    var last_trial_data = jsPsych.data.get().last(1).values()[0];
    console.log(last_trial_data.prompt)
    quiz_continue.stimulus = last_trial_data.prompt;}}

var quiz_q_1_ask = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_11_q1_ask.m4a",
  prompt: "<p>How do you win extra money?</p><ol type='A'><li>Visiting more planets</li><li>Staying at home base longer</li><li>Collecting more gems</li></ol>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_1_ask";}
 }

var quiz_q_1_answer = {
  type:'audio-keyboard-response',
  //html:"<p>How do you win extra money?</p><input type='radio' name='Q0' value='A'>A. Visiting more planets<br><input type='radio' name='Q0' value='B'>B. Staying at home base longer<br><input type='radio' name='Q0' value='C'>C. Collecting more gems<br><br><br><br>",
  prompt: "<p>How do you win extra money?</p><ol type='A'><li>Visiting more planets</li><li>Staying at home base longer</li><li>Collecting more gems</li></ol>",
  //button_label:'continue',
  choices: ['space'],
  on_finish: function(data) {
    //var answers_dict = JSON.parse(data.responses);
    //if (answers_dict["Q0"] == 'C') {
      //jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_1_fb_correct,quiz_continue,quiz_q_2_ask,quiz_q_2_answer],}, jsPsych.resumeExperiment);
    //} else {
      //jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_1_fb_incorrect,quiz_continue,quiz_q_2_ask,quiz_q_2_answer],}, jsPsych.resumeExperiment);
      //window.q_missed = q_missed + 1;}
    if (answers_dict["Q0"] == 'C') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_1_fb_correct,quiz_continue,quiz_q_2_ask,quiz_q_2_answer],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_1_fb_incorrect,quiz_continue,quiz_q_2_ask,quiz_q_2_answer],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;}
  }};

var quiz_q_1_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_12_q1_corrrect.m4a",
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
  stimulus: "run_exp/static/audio/clip_13_q1_incorrrect.m4a",
  prompt: "<p>That’s incorrect. You win extra money by collecting more gems.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.prompt = "<p>That’s incorrect. You win extra money by collecting more gems.</p>";
    data.trial_type = "quiz_q_1_fb_incorrect";}
  }

var quiz_q_2_ask = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_14_q2_ask.m4a",
  prompt: "<p>The length of this experiment</p><ol type='A'><li>Depends on how many planets you've visited</li><li>is 20 minutes no matter what</li><li>depends on how many gems you’ve collected</li></ol>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_2_ask";}
  }

var quiz_q_2_answer = {
  type:'survey-html-form',
  html:"<p>The length of this experiment</p><input type='radio' name='Q0' value='A'>A. Depends on how many planets you’ve visited<br><input type='radio' name='Q0' value='B'>B. is 20 minutes no matter what<br><input type='radio' name='Q0' value='C'>C. depends on how many gems you’ve collected<br><br><br><br>",
  button_label:'continue',
  on_finish: function(data) {
    var answers_dict = JSON.parse(data.responses);
    console.log('q 2 ')
    console.log(q_missed)
    if (answers_dict["Q0"] == 'B') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_2_fb_correct,quiz_continue,quiz_q_3_ask,quiz_q_3_answer],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_2_fb_incorrect,quiz_continue,quiz_q_3_ask,quiz_q_3_answer],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;
    }}
  };

var quiz_q_2_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_15_q2_correct.m4a",
  prompt: "<p>That’s correct. The experiment is 20 minutes no matter what.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_2_fb_correct";
    data.prompt = "<p>That’s correct. The experiment is 20 minutes no matter what.</p>";}
  }

var quiz_q_2_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_16_q2_incorrect.m4a",
  prompt: "<p>That’s incorrect. The experiment is 20 minutes no matter what.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_2_fb_incorrect";
    data.prompt = "<p>That’s incorrect. The experiment is 20 minutes no matter what.</p>";}
  }

var quiz_q_3_ask = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_17_q3_ask.m4a",
  prompt: "<p>You press what letter on your keyboard to travel to a new planet?</p><ol type='A'><li>the letter A</li><li>the letter L</li></ol>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_3_ask";}
  }


var quiz_q_3_answer = {
  type:'survey-html-form',
  html:"<p>You press what letter on your keyboard to travel to a new planet?</p><input type='radio' name='Q0' value='A'>A. the letter A<br><input type='radio' name='Q0' value='B'>B. the letter L<br><br><br><br>",
  button_label:'continue',
  on_finish: function(data) {
    var answers_dict = JSON.parse(data.responses);
    console.log('q 3 ')
    console.log(q_missed)
    if (answers_dict["Q0"] == 'B') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_3_fb_correct,quiz_continue,quiz_q_4_ask,quiz_q_4_answer],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_3_fb_incorrect,quiz_continue,quiz_q_4_ask,quiz_q_4_answer],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;
    }}
  };

var quiz_q_3_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_18_q3_correct.m4a",
  prompt: "<p> That’s correct. You press the letter L to travel to a new planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_3_fb_correct";
    data.prompt = "<p> That’s correct. You press the letter L to travel to a new planet.</p>";}
  };

var quiz_q_3_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_19_q3_incorrect.m4a",
  prompt: "<p>That’s incorrect.  You press the letter L to travel to a new planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_3_fb_incorrect";
    data.prompt = "<p>That’s incorrect.  You press the letter L to travel to a new planet.</p>";}
  };


var quiz_q_4_ask = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_20_q4_ask.m4a",
  prompt: "<p>The more you dig on a planet the fewer gems you’ll get with each dig.</p><ol type='A'><li>True</li><li>False</li></ol>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_4_ask";}
  }


var quiz_q_4_answer = {
  type:'survey-html-form',
  html:"<p>The more you dig on a planet the fewer gems you’ll get with each dig.</p><input type='radio' name='Q0' value='A'>A. True<br><input type='radio' name='Q0' value='B'>B. False<br><br><br><br>",
  button_label:'continue',
  on_finish: function(data) {
    var answers_dict = JSON.parse(data.responses);
    console.log('q 4 ')
    console.log(q_missed)
    if (answers_dict["Q0"] == 'A') {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_4_fb_correct,quiz_continue,quiz_q_5_ask,quiz_q_5_answer],}, jsPsych.resumeExperiment);
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_4_fb_incorrect,quiz_continue,quiz_q_5_ask,quiz_q_5_answer],}, jsPsych.resumeExperiment);
      window.q_missed = q_missed + 1;
    }}
  };

var quiz_q_4_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_21_q4_correct.m4a",
  prompt: "<p> That’s correct. The more you dig on a planet the fewer gems you’ll get with each dig. </p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_4_fb_correct";
    data.prompt = "<p> That’s correct. The more you dig on a planet the fewer gems you’ll get with each dig. </p>";}
  };

var quiz_q_4_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_22_q4_incorrect.m4a",
  prompt: "<p>That’s incorrect.  The more you dig on a planet the fewer gems you’ll get with each dig.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_4_fb_incorrect";
    data.prompt = "<p>That’s incorrect.  The more you dig on a planet the fewer gems you’ll get with each dig.</p>";}
  };
var quiz_q_5_ask = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_23_q5_ask.m4a",
  prompt: "<p>Does the alien tell you anything about how much treasure is on the planet?</p><ol type='A'><li>Yes</li><li>No</li></ol>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_5_ask";}
  }


var quiz_q_5_answer = {
  type:'survey-html-form',
  html:"<p>Does the alien tell you anything about how much treasure is on the planet?</p><input type='radio' name='Q0' value='A'>A. Yes<br><input type='radio' name='Q0' value='B'>B. No<br><br><br><br>",
  button_label:'continue',
  on_finish: function(data) {
  var answers_dict = JSON.parse(data.responses);
  console.log('q 5 ')
  console.log(q_missed)
  if (answers_dict["Q0"] == 'B') {
    jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_5_fb_correct,quiz_continue],}, jsPsych.resumeExperiment);
  } else {
    jsPsych.addNodeToEndOfTimeline({timeline: [quiz_q_5_fb_incorrect,quiz_continue],}, jsPsych.resumeExperiment);
    window.q_missed = q_missed + 1;
  }
  console.log(q_missed)

  if (q_missed > 0) {
    console.log(num_quiz_failures)
    if (num_quiz_failures < 2) {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_incorrect,quiz_incorrect_continue,quiz_q_1_ask,quiz_q_1_answer],}, jsPsych.resumeExperiment);
      window.num_quiz_failures= num_quiz_failures + 1;
    } else {
      jsPsych.addNodeToEndOfTimeline({timeline: [quiz_correct,quiz_correct_continue,instructions_begin_exp,instructions_begin_exp_continue],}, jsPsych.resumeExperiment);}
  } else {
    jsPsych.addNodeToEndOfTimeline({timeline: [quiz_correct,quiz_correct_continue,instructions_begin_exp,instructions_begin_exp_continue],}, jsPsych.resumeExperiment);}
  window.q_missed = 0;
  }};

var quiz_q_5_fb_correct = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_24_q5_correct.m4a",
  prompt: "<p> That’s correct. The alien tells you nothing about how much treasure is on the planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_5_fb_correct";
    data.prompt = "<p> That’s correct. The alien tells you nothing about how much treasure is on the planet.</p>";}
  };

var quiz_q_5_fb_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_25_q5_incorrect.m4a",
  prompt: "<p>That’s incorrect. The alien tells you nothing about how much treasure is on the planet.</p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_q_5_fb_incorrect";
    data.prompt = "<p>That’s incorrect. The alien tells you nothing about how much treasure is on the planet.</p>";}
  };

var quiz_correct = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_26_correct_quiz.m4a",
  prompt: "<p><strong>Good job! You're now ready to move on to the real game!</strong></p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_correct";}
  }


var quiz_correct_continue = {
  type:'html-button-response',
  stimulus:"<p><strong>Good job! You're now ready to move on to the real game!</strong></p>",
  choices:['continue'],
  on_finish: function(data) {
      data.trial_type = 'quiz_correct_continue';}
  }


var quiz_incorrect = {
  type:'audio-keyboard-response',
  stimulus: "run_exp/static/audio/clip_27_incorrect_quiz.m4a",
  prompt: "<p><strong>Oops, you missed some questions.</strong></p><p><strong>We want to make sure you know all the rules of the game, so you'll have to re-take the quiz.</strong></p>",
  choices: jsPsych.NO_KEYS,
  trial_ends_after_audio: true,
  on_finish: function(data) {
    data.trial_type = "quiz_incorrect";}}


var quiz_incorrect_continue = {
  type:'html-button-response',
  stimulus:"<p><strong>Oops, you missed some questions.</strong></p><p><strong>We want to make sure you know all the rules of the game, so you'll have to re-take the quiz.</strong></p>",
  choices: ['re-take the quiz'],
  on_finish: function(data) {
    data.trial_type = 'quiz_incorrect_continue';
    window.num_quiz_failures= num_quiz_failures + 1;}
 }
