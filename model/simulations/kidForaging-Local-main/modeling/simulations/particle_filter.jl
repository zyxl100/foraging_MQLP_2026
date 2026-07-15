using Random, Distributions

mutable struct Particle
    hyper_mu
    hyper_var
    hyper_tau
    cluster_mean
    cluster_variance
    cluster_points
    cluster_counts
    tau
end


##### MAKE PARTICLE FILTER ##############################
function init_particle_filter(num_particles::Int64,hyper_mu::Float64, hyper_var::Float64, hyper_tau::Float64, alpha::Float64)
    cluster_mean = [hyper_mu]
    cluster_var = [hyper_var]
    cluster_points = [[]]
    cluster_counts = [0]
    tau = [hyper_tau]

    all_particles = [Particle(hyper_mu,hyper_var,hyper_tau,cluster_mean,cluster_var,cluster_points,cluster_counts,tau)
    for p in 1:num_particles]

    weights = ones((num_particles))*(1/num_particles)

    return all_particles, weights
end

##### PRIOR ##############################


function log_prior_particle(particle::Particle,N::Int64,alpha::Float64)
    max_cluster = length(particle.cluster_counts)
    particle_prior = zeros(max_cluster+1)
    if N == 0
        particle_prior[1] = log(0.999999)
        particle_prior[2] = log(1-0.999999)
    else
        for k in 1:max_cluster
            particle_prior[k] = log(particle.cluster_counts[k]/(N+alpha))
        end
        particle_prior[max_cluster+1] = log(alpha/(N+alpha))
    end
    return particle_prior
end

function prior(particle_filter::Vector{Particle}, N::Int64, alpha::Float64)
  # prior prob of a cluster is proportional to number of members in clusters
  # prior prob of a new cluster is proportional to alpha
  num_particles = length(particle_filter)
  prior = [[] for i = 1:num_particles]
  for p in 1:num_particles
    curr_particle = particle_filter[p]
    prior[p] = exp.(log_prior_particle(curr_particle,N,alpha))/sum(exp.(log_prior_particle(curr_particle,N,alpha)))
  end
  #prinln('prior')
  #println(prior)
  return prior
end

##### LIKELIHOOD ##############################

function ll_data(mu::Float64,sigma::Float64,data::Any)
    d = Normal(mu,sigma) # errors here 
    return sum(logpdf.(d,data))
end

function log_likelihood_particle(particle::Particle,data::Vector{Any})
    max_cluster = length(particle.cluster_mean)
    particle_ll = zeros(max_cluster + 1)
    for k in 1:max_cluster
        mu = particle.cluster_mean[k]
        if particle.cluster_variance[k] <= 0 # ensure non-zero
            sigma = 0.000001
        else 
            sigma = particle.cluster_variance[k]^(1/2)
        end
        particle_ll[k] = ll_data(mu,sigma,data)
    end

    mu = particle.hyper_mu
    sigma = particle.hyper_var^(1/2)

    particle_ll[max_cluster+1] = ll_data(mu,sigma,data)
    return particle_ll
end



##### PARTICLE WEIGHTS ##############################

function log_likelihood_partition(particle::Particle)
    log_lik = 0
    for k in 1:length(particle.cluster_points)
        members = particle.cluster_points[k] # flatten to avoid loop here
        mu = particle.cluster_mean[k]
        if particle.cluster_variance[k] <= 0 # ensure non-zero
            sigma = 0.000001
        else 
            sigma = particle.cluster_variance[k]^(1/2)
        end
        for member in members
            log_lik += ll_data(mu,sigma,member)
        end
    end
    return log_lik
end

##### POSTERIOR ##############################

function normalize(post::Vector{Vector{Any}},eta::Vector{Any})
    for k in keys(post)
        post[k] = post[k]/eta
    end
    return post
end


##### CLUSTER UPDATE ##############################

function mean_square_error(data::Vector{Any})
    mu = mean(data)
    square_error = 0
    for d in data
        square_error = square_error + ((d-mu)^2)
    end
    return square_error
end

function cluster_param_update(particle::Particle,cluster::Int64,data::Vector{Any})
    prior_mu = particle.cluster_mean[cluster]
    prior_var = particle.cluster_variance[cluster]
    prior_tau = particle.tau[cluster]
    prior_n = length(particle.cluster_points[cluster])
    n = length(data)
    mu_bar = mean(data)


   # https://en.wikipedia.org/wiki/Normal_distribution#With_unknown_mean_and_unknown_variance
    posterior_mu = (prior_n*prior_mu + n*mu_bar)/(prior_n +n)
    posterior_n = prior_n +n
    posterior_tau = prior_tau + n
    posterior_tau_var = prior_tau*prior_var +  mean_square_error(data) + (((prior_n*n)/(prior_n +n))*((prior_mu - mu_bar)^2))
    posterior_var = posterior_tau_var/posterior_tau


    return posterior_mu, posterior_var, posterior_tau
end


######## RESAMPLE PARTICLES ############################################################

function particle_weights(particle_filter::Vector{Particle})
    num_particles = length(particle_filter)
    weights = zeros(num_particles)
    for p in 1:num_particles
      curr_particle = particle_filter[p]
      log_lik = log_likelihood_partition(curr_particle)
      weights[p] = log_lik
    end
    return weights/sum(weights)
end


function resample_and_update_particles(particle_filter::Vector{Particle},weights::Vector{Float64},post::Vector{Vector{Any}},data::Vector{Any})
    old_old_particles = deepcopy(particle_filter)
    cum_weight = cumsum(weights)
    num_particles = length(particle_filter)
    for p in 1:num_particles
        old_particles = deepcopy(old_old_particles)
        sampled_particle = argmax(rand() .< cum_weight) # try another way to make sure it works
        particle_filter[p] = old_particles[sampled_particle]

        # do cluster assignment based on the most likely cluster according to the posterior of the sample particle
        cum_particle_post = cumsum(post[sampled_particle])
        cluster = argmax(rand() .< cum_particle_post) # try another way to make sure it works

        # if inferring a new cluster
        if (cluster > length(particle_filter[p].cluster_mean))
            append!(particle_filter[p].cluster_mean,particle_filter[p].hyper_mu)
            append!(particle_filter[p].cluster_variance,particle_filter[p].hyper_var)
            push!(particle_filter[p].cluster_points,data)
            append!(particle_filter[p].cluster_counts,1)
            append!(particle_filter[p].tau,particle_filter[p].hyper_tau)
        else
            particle_filter[p].cluster_counts[cluster] = particle_filter[p].cluster_counts[cluster] + 1
            particle_filter[p].cluster_points[cluster] = append!(particle_filter[p].cluster_points[cluster],data)

        end

        posterior_mu, posterior_var, posterior_tau = cluster_param_update(particle_filter[p],cluster,data)
        particle_filter[p].cluster_mean[cluster] = posterior_mu
        particle_filter[p].cluster_variance[cluster] = posterior_var
        particle_filter[p].tau[cluster] = posterior_tau
    end

    new_weights = particle_weights(particle_filter)
    return particle_filter, new_weights
end

