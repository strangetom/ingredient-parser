Resources
=========

This page lists various resources that I've found useful, interesting or related.

Blog Posts
^^^^^^^^^^

* `Extracting Structured Data From Recipes Using Conditional Random Fields <https://archive.nytimes.com/open.blogs.nytimes.com/2015/04/09/extracting-structured-data-from-recipes-using-conditional-random-fields>`_ (archive.nytimes.com, 2015)

  A blog post from the New York Times describing using a Condition Random Fields model to label ingredient sentences. This is the original work that inspired this package.

* `Resurrecting a Dead Library: Part One - Resuscitation <https://mtlynch.io/resurrecting-1/>`_ (mtlynch.io, 2018)

  Part 1 of a series of 3 blog posts describing how the New York Times work above was resurrected and modernised, leading to the https://zestfuldata.com/ API.

* `Statistical NLP on OpenStreetMap <https://medium.com/@albarrentine/statistical-nlp-on-openstreetmap-b9d573e6cc86>`_ (medium.com, 2016)

  The first of two blog posts describing how the `libpostal <https://github.com/openvenues/libpostal>`_ uses natural language processing to parse addresses. The are many similarities between the approaches libpostal and this package take.

  `Issue 164 <https://github.com/openvenues/libpostal/issues/164>`_ on the libpostal repository provides some further insight into how they extract the features used for their model.

Papers
^^^^^^

* `TASTEset -- Recipe Dataset and Food Entities Recognition Benchmark <https://arxiv.org/abs/2204.07775>`_ (arxiv.org, 2022)

    Food Computing is currently a fast-growing field of research. Natural language processing (NLP) is also increasingly essential in this field, especially for recognising food entities. However, there are still only a few well-defined tasks that serve as benchmarks for solutions in this area. We introduce a new dataset -- called *TASTEset* -- to bridge this gap. In this dataset, Named Entity Recognition (NER) models are expected to find or infer various types of entities helpful in processing recipes, e.g.~food products, quantities and their units, names of cooking processes, physical quality of ingredients, their purpose, taste.

    The dataset consists of 700 recipes with more than 13,000 entities to extract. We provide a few state-of-the-art baselines of named entity recognition models, which show that our dataset poses a solid challenge to existing models. The best model achieved, on average, 0.95 F1 score, depending on the entity type -- from 0.781 to 0.982. We share the dataset and the task to encourage progress on more in-depth and complex information extraction from recipes.

* `Ingredient Extraction from Text in the Recipe Domain. <http://arxiv.org/abs/2204.08137>`_ (arxiv.org, 2022)

    In recent years, there has been an increase in the number of devices with virtual assistants (e.g: Siri, Google Home, Alexa) in our living rooms and kitchens. As a result of this, these devices receive several queries about recipes. All these queries will contain terms relating to a "recipe-domain" i.e: they will contain dish-names, ingredients, cooking times, dietary preferences etc. Extracting these recipe-relevant aspects from the query thus becomes important when it comes to addressing the user's information need. Our project focuses on extracting ingredients from such plain-text user utterances. Our best performing model was a fine-tuned BERT which achieved an F1-score of 95.01. We have released all our code in a GitHub repository.

* `MenuNER: Domain-Adapted BERT Based NER Approach for a Domain with Limited Dataset and Its Application to Food Menu Domain <dx.doi.org/10.3390/app11136007>`_ (dx.doi.org, 2021)

    Entity-based information extraction is one of the main applications of Natural Language Processing (NLP). Recently, deep transfer-learning utilizing contextualized word embedding from pre-trained language models has shown remarkable results for many NLP tasks, including Named entity recognition (NER). BERT (Bidirectional Encoder Representations from Transformers) is gaining prominent attention among various contextualized word embedding models as a state-of-the-art pre-trained language model. It is quite expensive to train a BERT model from scratch for a new application domain since it needs a huge dataset and enormous computing time. In this paper, we focus on menu entity extraction from online user reviews for the restaurant and propose a simple but effective approach for NER task on a new domain where a large dataset is rarely available or difficult to prepare, such as food menu domain, based on domain adaptation technique for word embedding and fine-tuning the popular NER task network model 'Bi-LSTM+CRF' with extended feature vectors. The proposed NER approach (named as 'MenuNER') consists of two step-processes: (1) Domain adaptation for target domain; further pre-training of the off-the-shelf BERT language model (BERT-base) in semi-supervised fashion on a domain-specific dataset, and (2) Supervised fine-tuning the popular Bi-LSTM+CRF network for downstream task with extended feature vectors obtained by concatenating word embedding from the domain-adapted pre-trained BERT model from the first step, character embedding and POS tag feature information. Experimental results on handcrafted food menu corpus from customers' review dataset show that our proposed approach for domain-specific NER task, that is: food menu named-entity recognition, performs significantly better than the one based on the baseline off-the-shelf BERT-base model. The proposed approach achieves 92.5% F1 score on the YELP dataset for the MenuNER task.

* `Efficient Training Methods For Conditional Random Fields <https://homepages.inf.ed.ac.uk/csutton/publications/sutton-thesis.pdf>`_ (ed.ac.uk, 2008)

    Many applications require predicting not a just a single variable, but multiple variables that depend on each other. Recent attention has therefore focused on structured prediction methods, which combine the modelling flexibility of graphical models with the ability to employ complex, dependent features typical of traditional classification methods. Especially popular have been conditional random fields (CRFs), which are graphical models of the conditional distribution over outputs given a set of observed features. Unfortunately, parameter estimation in CRFs requires repeated inference, which can be computationally expensive. Complex graphical structures are increasingly desired in practical applications, but then training time often becomes prohibitive.

    In this thesis, I investigate efficient training methods for conditional random fields with complex graphical structure, focusing on local methods which avoid propagating information globally along the graph. First, I investigate piecewise training, which trains each of a model's factors separately. I present three views of piecewise training: as maximizing the likelihood in a so-called “node-split graph”, as maximizing the Bethe likelihood with uniform messages, and as generalizing the pseudo-moment matching estimator of Wainwright, Jaakkola, and Willsky. Second, I propose piecewise pseudolikelihood, a hybrid procedure which "pseudolikelihood-izes" the piecewise likelihood, and is therefore more efficient if the variables have large cardinality. Piecewise pseudolikelihood performs well even on applications in which standard pseudo-likelihood performs poorly. Finally, motivated by the connection between piecewise training and BP, I explore training methods using beliefs arising from stopping BP before convergence. I propose a new schedule for message propagation that improves upon the dynamic schedule proposed recently by Elidan, McGraw, and Koller, and present suggestive results applying dynamic schedules to the system of equations that combine inference and learning.

    I also present two novel families of loopy CRFs, which appear as test cases throughout. First is the dynamic CRF, which combines the factorized state representation of dynamic Bayesian networks with the modelling flexibility of conditional models. The second of these is the skip-chain CRF, which models the fact that identical words are likely to have the same label, even if they occur far apart.
