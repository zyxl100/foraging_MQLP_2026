%% Moving logistic regression across all subjects for multiple predictors
clear; clc; close all;

% -------------------------------------------------------------------------
% PARAMETERS
% -------------------------------------------------------------------------
%data_dir = 'C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\Threat Foraging Task and Projects\prey-foraging-main\WebZorn\data\April2025\results_complete_for_logreg';
data_dir = 'C:\Users\zyfxl\OneDrive - UC Irvine\UCI\CCNL Lab\Foraging Task Overview\Threat Foraging Task and Projects\prey-foraging-main\WebZorn\data\Pilot2_August2025\results_complete_for_logreg';
win_len  = 30;
step_sz  = 20;

% Variables to fit (predictors)
predictor_names = { ...
    'vForage_optimal', ...
    'vWait_optimal', ...
    'vForage_hardavoid', ...
    'vWait_hardavoid', ...
    'vDiff', ...
    'vDiff_optimal', ...
    'vDiff_hardavoid'};

% -------------------------------------------------------------------------
% LOAD FILES
% -------------------------------------------------------------------------
files = dir(fullfile(data_dir, 'results*.csv'));
nSubs = numel(files);
if nSubs == 0
    error('No results*.csv files found in %s', data_dir);
end
fprintf('Found %d subject files.\n', nSubs);

% -------------------------------------------------------------------------
% LOOP OVER PREDICTORS
% -------------------------------------------------------------------------
for p = 1:numel(predictor_names)
    predictor = predictor_names{p};
    fprintf('\nProcessing predictor: %s\n', predictor);

    all_betas = cell(nSubs,1);
    all_r2    = cell(nSubs,1);
    all_centers = cell(nSubs,1);

    % ---------------- Subject loop ----------------
    for s = 1:nSubs
        fname = fullfile(data_dir, files(s).name);
        data = readtable(fname);

        % Skip subjects missing predictor or choice
        if ~all(ismember({predictor, 'choice'}, data.Properties.VariableNames))
            warning('Skipping %s (missing %s or choice)', files(s).name, predictor);
            continue;
        end

        X = data.(predictor);
        y = data.choice;
        n = length(y);

        win_starts = 1:step_sz:(n - win_len + 1);
        nWins = numel(win_starts);
        betas = NaN(nWins,1);
        r2s   = NaN(nWins,1);
        centers = NaN(nWins,1);

        for w = 1:nWins
            idx = win_starts(w):(win_starts(w)+win_len-1);
            xw = X(idx);
            yw = y(idx);

            mdl = fitglm(xw, yw, 'Distribution','binomial','Link','logit');
            betas(w) = mdl.Coefficients.Estimate(2);

            % McFadden pseudo-R²
            ll_full = mdl.LogLikelihood;
            mdl_null = fitglm(zeros(size(xw)), yw, 'Distribution','binomial','Link','logit');
            ll_null = mdl_null.LogLikelihood;
            r2s(w) = 1 - (ll_full / ll_null);

            centers(w) = mean(idx);
        end

        all_betas{s}   = betas;
        all_r2{s}      = r2s;
        all_centers{s} = centers;
    end

    % ---------------- Align variable-length subjects ----------------
    maxWins = max(cellfun(@length, all_betas));
    B = NaN(nSubs, maxWins);
    R = NaN(nSubs, maxWins);
    C = NaN(nSubs, maxWins);

    for s = 1:nSubs
        L = length(all_betas{s});
        B(s,1:L) = all_betas{s};
        R(s,1:L) = all_r2{s};
        C(s,1:L) = all_centers{s};
    end

    meanB = nanmean(B,1);
    semB  = nanstd(B,[],1) ./ sqrt(sum(~isnan(B),1));
    meanR = nanmean(R,1);
    semR  = nanstd(R,[],1) ./ sqrt(sum(~isnan(R),1));
    meanC = nanmean(C,1);

    valid = ~isnan(meanC);
    meanC = meanC(valid);
    meanB = meanB(valid); semB = semB(valid);
    meanR = meanR(valid); semR = semR(valid);

    % ---------------- Plot for this predictor ----------------
    figure('Position',[200 100 950 450]);

    subplot(2,1,1);
    errorbar(meanC, meanB, semB, 'o-','LineWidth',1.5,'MarkerFaceColor',[0.2 0.4 0.8]);
    xlabel('Trial (window center)');
    ylabel('\beta coefficient');
    title(sprintf('Moving logistic regression β — %s', predictor),'Interpreter','none');
    grid on;

    subplot(2,1,2);
    errorbar(meanC, meanR, semR, 's-','LineWidth',1.5,'MarkerFaceColor',[0.3 0.6 0.3]);
    xlabel('Trial (window center)');
    ylabel('Pseudo-R^2 (McFadden)');
    title(sprintf('Model fit — %s', predictor),'Interpreter','none');
    grid on;

    sgtitle(sprintf('%s | Moving logistic regression (win=%d, step=%d, N=%d)', ...
        predictor, win_len, step_sz, nSubs), 'Interpreter','none');

    % Optionally, save each figure
    saveas(gcf, fullfile(data_dir, sprintf('moving_logreg_%s.png', predictor)));
end
