#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       cbcBayesPostProc.py
#
#       Copyright 2010
#       Benjamin Aylott <benjamin.aylott@ligo.org>,
#       Will M. Farr <will.farr@ligo.org>,
#       John Veitch <john.veitch@ligo.org>
#
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

#===============================================================================
# Preamble
#===============================================================================

#standard library imports
import sys
import os

from math import ceil,floor
import cPickle as pickle

from time import strftime

#related third party imports
from numpy import array,exp,cos,sin,arcsin,arccos,sqrt,size,mean,column_stack,cov,unique,hsplit,correlate,log

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt

#local application/library specific imports
from pylal import SimInspiralUtils
from pylal import bayespputils as bppu
from pylal import git_version

__author__="Ben Aylott <benjamin.aylott@ligo.org>, Will M. Farr <will.farr@ligo.org>, John Veitch <john.veitch@ligo.org>"
__version__= "git id %s"%git_version.id
__date__= git_version.date

def pickle_to_file(obj,fname):
    """
    Pickle/serialize 'obj' into 'fname'.
    """
    filed=open(fname,'w')
    pickle.dump(obj,filed)
    filed.close()

def oneD_dict_to_file(dict,fname):
    filed=open(fname,'w')
    for key,value in dict.items():
        filed.write("%s %s\n"%(str(key),str(value)) )

def cbcBayesPostProc(
                        outdir,data,oneDMenu,twoDGreedyMenu,GreedyRes,
                        confidence_levels,twoDplots,
                        #misc. optional
                        injfile=None,eventnum=None,skyres=None,
                        #direct integration evidence
                        dievidence=False,boxing=64,difactor=1.0,
                        #manual input of bayes factors optional.
                        bayesfactornoise=None,bayesfactorcoherent=None,
                        #nested sampling options
                        ns_flag=False,ns_xflag=False,ns_Nlive=None,
                        #spinspiral/mcmc options
                        ss_flag=False,ss_deltaLogL=None,ss_spin_flag=False,
                        #lalinferenceMCMC options
                        li_flag=False,nDownsample=1,
                        #followupMCMC options
                        fm_flag=False,
                        # on ACF?
                        noacf=False
                    ):
    """
    This is a demonstration script for using the functionality/data structures
    contained in pylal.bayespputils . It will produce a webpage from a file containing
    posterior samples generated by the parameter estimation codes with 1D/2D plots
    and stats from the marginal posteriors for each parameter/set of parameters.
    """

    if eventnum is not None and injfile is None:
        print "You specified an event number but no injection file. Ignoring!"

    if data is None:
        print 'You must specify an input data file'
        exit(1)
    #
    if outdir is None:
        print "You must specify an output directory."
        exit(1)

    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    #

    if fm_flag:
        peparser=bppu.PEOutputParser('fm')
        commonResultsObj=peparser.parse(data)

    elif ns_flag and not ss_flag:
        peparser=bppu.PEOutputParser('ns')
        commonResultsObj=peparser.parse(data,Nlive=ns_Nlive,xflag=ns_xflag)

    elif ss_flag and not ns_flag:
        peparser=bppu.PEOutputParser('mcmc_burnin')
        commonResultsObj=peparser.parse(data,spin=ss_spin_flag,deltaLogL=ss_deltaLogL)

    elif li_flag:
        peparser=bppu.PEOutputParser('inf_mcmc')
        commonResultsObj=peparser.parse(data,deltaLogL=ss_deltaLogL,nDownsample=nDownsample)

    elif ss_flag and ns_flag:
        print "Undefined input format. Choose only one of:"
        exit(1)

    else:
        peparser=bppu.PEOutputParser('common')
        commonResultsObj=peparser.parse(open(data[0],'r'))
    #Select injections using tc +/- 0.1s if it exists or eventnum from the injection file
    injection=None
    if injfile:
        import itertools
        injections = SimInspiralUtils.ReadSimInspiralFromFiles([injfile])
        if eventnum is not None:
            if(len(injections)<eventnum):
                print "Error: You asked for event %d, but %s contains only %d injections" %(eventnum,injfile,len(injections))
                sys.exit(1)
            else:
                injection=injections[eventnum]


    ## Load Bayes factors ##
    # Add Bayes factor information to summary file #
    if bayesfactornoise is not None:
        bfile=open(bayesfactornoise,'r')
        BSN=bfile.read()
        bfile.close()
        print 'BSN: %s'%BSN
    if bayesfactorcoherent is not None:
        bfile=open(bayesfactorcoherent,'r')
        BCI=bfile.read()
        bfile.close()
        print 'BCI: %s'%BCI

    #Create an instance of the posterior class using the posterior values loaded
    #from the file and any injection information (if given).
    pos = bppu.Posterior(commonResultsObj,SimInspiralTableEntry=injection)
    print "pos names " + str(pos.names) +"\n"

    if eventnum is None and injfile is not None:
        import itertools
        injections = SimInspiralUtils.ReadSimInspiralFromFiles([injfile])

        if(len(injections)<1):
            try:
                print 'Warning: Cannot find injection with end time %f' %(pos['time'].mean)
            except KeyError:
                print "Warning: No 'time' column!"

        else:
            try:
                injection = itertools.ifilter(lambda a: abs(float(a.get_end()) - pos['time'].mean) < 0.1, injections).next()
                pos.set_injection(injection)
            except KeyError:
                print "Warning: No 'time' column!"

    #Stupid bit to generate component mass posterior samples (if they didnt exist already)
    if ('mc' in pos.names or 'mchirp' in pos.names) and \
    'eta' in pos.names and \
    ('mass1' not in pos.names or 'm1' not in pos.names) and\
    ('m2' not in pos.names or 'm2' not in pos.names):

        if 'mc' in pos.names:
            mchirp_name='mc'
        else:
            mchirp_name='mchirp'

        inj_mass1=None
        inj_mass2=None
        if injection:
            inj_mass1,inj_mass2=bppu.mc2ms(injection.mchirp,injection.eta)

        mass1_samps,mass2_samps=bppu.mc2ms(pos[mchirp_name].samples,pos['eta'].samples)
        mass1_pos=bppu.OneDPosterior('m1',mass1_samps,injected_value=inj_mass1)
        mass2_pos=bppu.OneDPosterior('m2',mass2_samps,injected_value=inj_mass2)

        pos.append(mass1_pos)
        pos.append(mass2_pos)


    ##Print some summary stats for the user...##
    #Number of samples
    print "Number of posterior samples: %i"%len(pos)
    # Means
    print 'Means:'
    print str(pos.means)
    #Median
    print 'Median:'
    print str(pos.medians)
    #maxL
    print 'maxL:'
    max_pos,max_pos_co=pos.maxL
    print max_pos_co

    #==================================================================#
    #Create web page
    #==================================================================#

    html=bppu.htmlPage('Posterior PDFs',css=bppu.__default_css_string)

    #Create a section for meta-data/run information
    html_meta=html.add_section('Summary')
    html_meta.p('Produced from '+str(len(pos))+' posterior samples.')
    if 'cycle' in pos.names:
        html_meta.p('Longest chain has '+str(pos.longest_chain_cycles())+' cycles.')
    filenames='Samples read from %s'%(data[0])
    if len(data) > 1:
        for fname in data[1:]:
            filenames+=', '+str(fname)
    html_meta.p(filenames)

    #Create a section for model selection results (if they exist)
    if bayesfactornoise is not None:
        html_model=html.add_section('Model selection')
        html_model.p('log Bayes factor ( coherent vs gaussian noise) = %s, Bayes factor=%f'%(BSN,exp(float(BSN))))
        if bayesfactorcoherent is not None:
            html_model.p('log Bayes factor ( coherent vs incoherent OR noise ) = %s, Bayes factor=%f'%(BCI,exp(float(BCI))))

    if dievidence:
        html_model=html.add_section('Direct Integration Evidence')
        ev=difactor*pos.di_evidence(boxing=boxing)
        evfilename=os.path.join(outdir,"evidence.dat")
        evout=open(evfilename,"w")
        evout.write(str(ev))
        evout.write(" ")
        evout.write(str(log(ev)))
        evout.close()
        print "Computing direct integration evidence = %g (log(Evidence) = %g)"%(ev, log(ev))
        html_model.p('Direct integration evidence is %g, or log(Evidence) = %g.  (Boxing parameter = %d.)'%(ev,log(ev),boxing))
        if 'logl' in pos.names:
            ev=pos.harmonic_mean_evidence()
            html_model.p('Compare to harmonic mean evidence of %g (log(Evidence) = %g).'%(ev,log(ev)))

    #Create a section for summary statistics
    html_stats=html.add_section('Summary statistics')
    html_stats.write(str(pos))

    #Create a section for the covariance matrix
    html_stats_cov=html.add_section('Covariance matrix')
    pos_samples,table_header_string=pos.samples()

    #calculate cov matrix
    cov_matrix=cov(pos_samples,rowvar=0,bias=1)

    #Create html table
    table_header_list=table_header_string.split()

    cov_table_string='<table border="1" id="covtable"><tr><th/>'
    for header in table_header_list:
        cov_table_string+='<th>%s</th>'%header
    cov_table_string+='</tr>'

    cov_column_list=hsplit(cov_matrix,cov_matrix.shape[1])

    for cov_column,cov_column_name in zip(cov_column_list,table_header_list):
        cov_table_string+='<tr><th>%s</th>'%cov_column_name
        for cov_column_element in cov_column:
            cov_table_string+='<td>%s</td>'%str(cov_column_element[0])
        cov_table_string+='</tr>'
    cov_table_string+='</table>'
    html_stats_cov.write(cov_table_string)

    #==================================================================#
    #Generate sky map
    #==================================================================#
    #If sky resolution parameter has been specified try and create sky map...
    skyreses=None
    sky_injection_cl=None
    if skyres is not None and 'ra' in pos.names and 'dec' in pos.names:
        #Greedy bin sky samples (ra,dec) into a grid on the sky which preserves
        #?
        top_ranked_sky_pixels,sky_injection_cl,skyreses,injection_area=bppu.greedy_bin_sky(pos,skyres,confidence_levels)
        print "BCI for sky area:"
        print skyreses
        #Create sky map in outdir
        bppu.plot_sky_map(top_ranked_sky_pixels,outdir)

        #Create a web page section for sky localization results/plots (if defined)

        html_sky=html.add_section('Sky Localization')
        if injection:
            if sky_injection_cl:
                html_sky.p('Injection found at confidence interval %f in sky location'%(sky_injection_cl))
            else:
                html_sky.p('Injection not found in posterior bins in sky location!')
        html_sky.write('<img width="35%" src="skymap.png"/>')

        html_sky_write='<table border="1" id="statstable"><tr><th>Confidence region</th><th>size (sq. deg)</th></tr>'

        fracs=skyreses.keys()
        fracs.sort()

        skysizes=[skyreses[frac] for frac in fracs]
        for frac,skysize in zip(fracs,skysizes):
            html_sky_write+=('<tr><td>%f</td><td>%f</td></tr>'%(frac,skysize))
        html_sky_write+=('</table>')

        html_sky.write(html_sky_write)

    #==================================================================#
    #1D posteriors
    #==================================================================#

    #Loop over each parameter and determine the contigious and greedy
    #confidence levels and some statistics.

    #Add section for 1D confidence intervals
    html_ogci=html.add_section('1D confidence intervals (greedy binning)')
    #Generate the top part of the table
    html_ogci_write='<table id="statstable" border="1"><tr><th/>'
    confidence_levels.sort()
    for cl in confidence_levels:
        html_ogci_write+='<th>%f</th>'%cl
    if injection:
        html_ogci_write+='<th>Injection Confidence Level</th>'
        html_ogci_write+='<th>Injection Confidence Interval</th>'
    html_ogci_write+='</tr>'

    #Add section for 1D marginal PDFs and sample plots
    html_ompdf=html.add_section('1D marginal posterior PDFs')
    #Table matter
    if not noacf:
        html_ompdf_write= '<table><tr><th>Histogram and Kernel Density Estimate</th><th>Samples used</th><th>Autocorrelation</th></tr>'
    else:
        html_ompdf_write= '<table><tr><th>Histogram and Kernel Density Estimate</th><th>Samples used</th></tr>'

    onepdfdir=os.path.join(outdir,'1Dpdf')
    if not os.path.isdir(onepdfdir):
        os.makedirs(onepdfdir)

    sampsdir=os.path.join(outdir,'1Dsamps')
    if not os.path.isdir(sampsdir):
        os.makedirs(sampsdir)

    for par_name in oneDMenu:
        par_name=par_name.lower()
        print "Binning %s to determine confidence levels ..."%par_name
        try:
            pos[par_name.lower()]
        except KeyError:
            print "No input chain for %s, skipping binning."%par_name
            continue
        try:
            par_bin=GreedyRes[par_name]
        except KeyError:
            print "Bin size is not set for %s, skipping binning."%par_name
            continue
        binParams={par_name:par_bin}

        toppoints,injectionconfidence,reses,injection_area,cl_intervals=bppu.greedy_bin_one_param(pos,binParams,confidence_levels)

        oneDContCL,oneDContInj = bppu.contigious_interval_one_param(pos,binParams,confidence_levels)

        #Generate new BCI html table row
        BCItableline='<tr><td>%s</td>'%(par_name)
        cls=reses.keys()
        cls.sort()

        for cl in cls:
            BCItableline+='<td>%f</td>'%reses[cl]

        if injection is not None:
            if injectionconfidence is not None and injection_area is not None:

                BCItableline+='<td>%f</td>'%injectionconfidence
                BCItableline+='<td>%f</td>'%injection_area

            else:
                BCItableline+='<td/>'
                BCItableline+='<td/>'

        BCItableline+='</tr>'

        #Append new table line to section html
        html_ogci_write+=BCItableline

        #Generate 1D histogram/kde plots
        print "Generating 1D plot for %s."%par_name
        oneDPDFParams={par_name:50}
        rbins,plotFig=bppu.plot_one_param_pdf(pos,oneDPDFParams)

        figname=par_name+'.png'
        oneDplotPath=os.path.join(onepdfdir,figname)
        plotFig.savefig(oneDplotPath)

        if rbins:
            print "r of injected value of %s (bins) = %f"%(par_name, rbins)

        ##Produce plot of raw samples
        myfig=plt.figure(figsize=(4,3.5),dpi=200)
        pos_samps=pos[par_name].samples
        if not ("chain" in pos.names) or fm_flag:
            # If there is not a parameter named "chain" in the
            # posterior, then just produce a plot of the samples.
            plt.plot(pos_samps,'.',figure=myfig)
            maxLen=len(pos_samps)
        else:
            # If there is a parameter named "chain", then produce a
            # plot of the various chains in different colors, with
            # smaller dots.
            data,header=pos.samples()
            par_index=pos.names.index(par_name)
            chain_index=pos.names.index("chain")
            chains=unique(pos["chain"].samples)
            chainData=[data[ data[:,chain_index] == chain, par_index ] for chain in chains]
            chainDataRanges=[range(len(cd)) for cd in chainData]
            maxLen=max([len(cd) for cd in chainData])
            for rng, data in zip(chainDataRanges, chainData):
                plt.plot(rng, data, marker=',',linewidth=0.0,figure=myfig)
            plt.title("Gelman-Rubin R = %g"%(pos.gelman_rubin(par_name)))
            
            #dataPairs=[ [rng, data] for (rng,data) in zip(chainDataRanges, chainData)]
            #flattenedData=[ item for pair in dataPairs for item in pair ]
            #maxLen=max([len(data) for data in flattenedData])
            #plt.plot(array(flattenedData),marker=',',linewidth=0.0,figure=myfig)


        injpar=pos[par_name].injval

        if injpar:
            if min(pos_samps)<injpar and max(pos_samps)>injpar:
                plt.axhline(injpar, color='r', linestyle='-.')
        myfig.savefig(os.path.join(sampsdir,figname.replace('.png','_samps.png')))

        if not (noacf):
            acffig=plt.figure(figsize=(4,3.5),dpi=200)
            if not ("chain" in pos.names):
                data=pos_samps[:,0]
                mu=mean(data)
                corr=correlate((data-mu),(data-mu),mode='full')
                N=len(data)
                plt.plot(corr[N-1:]/corr[N-1], figure=acffig)
            else:
                for rng, data in zip(chainDataRanges, chainData):
                    mu=mean(data)
                    corr=correlate(data-mu,data-mu,mode='full')
                    N=len(data)
                    plt.plot(corr[N-1:]/corr[N-1], figure=acffig)

            acffig.savefig(os.path.join(sampsdir,figname.replace('.png','_acf.png')))

        if not noacf:
            html_ompdf_write+='<tr><td><img src="1Dpdf/'+figname+'"/></td><td><img src="1Dsamps/'+figname.replace('.png','_samps.png')+'"/></td><td><img src="1Dsamps/'+figname.replace('.png', '_acf.png')+'"/></td></tr>'
        else:
            html_ompdf_write+='<tr><td><img src="1Dpdf/'+figname+'"/></td><td><img src="1Dsamps/'+figname.replace('.png','_samps.png')+'"/></td></tr>'


    html_ompdf_write+='</table>'

    html_ompdf.write(html_ompdf_write)

    html_ogci_write+='</table>'
    html_ogci.write(html_ogci_write)

    #==================================================================#
    #2D posteriors
    #==================================================================#

    #Loop over parameter pairs in twoDGreedyMenu and bin the sample pairs
    #using a greedy algorithm . The ranked pixels (toppoints) are used
    #to plot 2D histograms and evaluate Bayesian confidence intervals.

    #Make a folder for the 2D kde plots
    margdir=os.path.join(outdir,'2Dkde')
    if not os.path.isdir(margdir):
        os.makedirs(margdir)

    twobinsdir=os.path.join(outdir,'2Dbins')
    if not os.path.isdir(twobinsdir):
        os.makedirs(twobinsdir)

    greedytwobinsdir=os.path.join(outdir,'greedy2Dbins')
    if not os.path.isdir(greedytwobinsdir):
        os.makedirs(greedytwobinsdir)

    #Add a section to the webpage for a table of the confidence interval
    #results.
    html_tcig=html.add_section('2D confidence intervals (greedy binning)')
    #Generate the top part of the table
    html_tcig_write='<table id="statstable" border="1"><tr><th/>'
    confidence_levels.sort()
    for cl in confidence_levels:
        html_tcig_write+='<th>%f</th>'%cl
    if injection:
        html_tcig_write+='<th>Injection Confidence Level</th>'
        html_tcig_write+='<th>Injection Confidence Interval</th>'
    html_tcig_write+='</tr>'

    #=  Add a section for a table of 2D marginal PDFs (kde)
    html_tcmp=html.add_section('2D Marginal PDFs')

    #Table matter
    html_tcmp_write='<table border="1">'

    row_count=0

    for par1_name,par2_name in twoDGreedyMenu:
        par1_name=par1_name.lower()
        par2_name=par2_name.lower()
        print "Binning %s-%s to determine confidence levels ..."%(par1_name,par2_name)
        try:
            pos[par1_name.lower()]
        except KeyError:
            print "No input chain for %s, skipping binning."%par1_name
            continue
        try:
            pos[par2_name.lower()]
        except KeyError:
            print "No input chain for %s, skipping binning."%par2_name
            continue
        #Bin sizes
        try:
            par1_bin=GreedyRes[par1_name]
        except KeyError:
            print "Bin size is not set for %s, skipping %s/%s binning."%(par1_name,par1_name,par2_name)
            continue
        try:
            par2_bin=GreedyRes[par2_name]
        except KeyError:
            print "Bin size is not set for %s, skipping %s/%s binning."%(par2_name,par1_name,par2_name)
            continue

        #Form greedy binning input structure
        greedy2Params={par1_name:par1_bin,par2_name:par2_bin}
        print "greedy2Params "+ str(greedy2Params) +"\n"
        #Greedy bin the posterior samples
        toppoints,injection_cl,reses,injection_area=\
        bppu.greedy_bin_two_param(pos,greedy2Params,confidence_levels)

        print "BCI %s-%s:"%(par1_name,par2_name)
        print reses

        #Generate new BCI html table row
        BCItableline='<tr><td>%s-%s</td>'%(par1_name,par2_name)
        cls=reses.keys()
        cls.sort()

        for cl in cls:
            BCItableline+='<td>%f</td>'%reses[cl]

        if injection is not None:
            if injection_cl is not None:
                BCItableline+='<td>%f</td>'%injection_cl
                BCItableline+='<td>'+str(injection_area)+'</td>'

            else:
                BCItableline+='<td/>'
                BCItableline+='<td/>'

        BCItableline+='</tr>'

        #Append new table line to section html
        html_tcig_write+=BCItableline


        #= Plot 2D histograms of greedily binned points =#

        greedy2ContourPlot=bppu.plot_two_param_greedy_bins_contour({'Result':pos},greedy2Params,[0.67,0.9,0.95],{'Result':'k'})
        greedy2ContourPlot.savefig(os.path.join(greedytwobinsdir,'%s-%s_greedy2contour.png'%(par1_name,par2_name)))

        greedy2HistFig=bppu.plot_two_param_greedy_bins_hist(pos,greedy2Params,confidence_levels)
        greedy2HistFig.savefig(os.path.join(greedytwobinsdir,'%s-%s_greedy2.png'%(par1_name,par2_name)))

        greedyFile = open(os.path.join(twobinsdir,'%s_%s_greedy_stats.txt'%(par1_name,par2_name)),'w')

        #= Write out statistics for greedy bins
        for cl in cls:
            greedyFile.write("%lf %lf\n"%(cl,reses[cl]))
        greedyFile.close()

        #= Generate 2D kde plots =#
        if [par1_name,par2_name] in twoDplots or [par2_name,par1_name] in twoDplots:
            print 'Generating %s-%s plot'%(par1_name,par2_name)

            par1_pos=pos[par1_name].samples
            par2_pos=pos[par2_name].samples

            if (size(unique(par1_pos))<2 or size(unique(par2_pos))<2):
                continue

            plot2DkdeParams={par1_name:50,par2_name:50}
            myfig=bppu.plot_two_param_kde(pos,plot2DkdeParams)

            figname=par1_name+'-'+par2_name+'_2Dkernel.png'
            twoDKdePath=os.path.join(margdir,figname)

            if row_count==0:
                html_tcmp_write+='<tr>'
            html_tcmp_write+='<td width="30%"><img width="100%" src="2Dkde/'+figname+'"/></td>'
            row_count+=1
            if row_count==3:
                html_tcmp_write+='</tr>'
                row_count=0

            myfig.savefig(twoDKdePath)


    #Finish off the BCI table and write it into the etree
    html_tcig_write+='</table>'
    html_tcig.write(html_tcig_write)
    #Finish off the 2D kde plot table
    while row_count!=0:
        html_tcmp_write+='<td/>'
        row_count+=1
        if row_count==3:
            row_count=0
            html_tcmp_write+='</tr>'
    html_tcmp_write+='</table>'
    html_tcmp.write(html_tcmp_write)
    #Add a link to all plots
    html_tcmp.a("2Dkde/",'All 2D marginal PDFs (kde)')

    html_footer=html.add_section('')
    html_footer.p('Produced using cbcBayesPostProc.py at '+strftime("%Y-%m-%d %H:%M:%S")+' .')

    cc_args=''
    for arg in sys.argv:
        cc_args+=arg+' '

    html_footer.p('Command line: %s'%cc_args)
    html_footer.p(git_version.verbose_msg)

    #Save results page
    resultspage=open(os.path.join(outdir,'posplots.html'),'w')
    resultspage.write(str(html))

    # Save posterior samples too...
    posfilename=os.path.join(outdir,'posterior_samples.dat')
    pos.write_to_file(posfilename)

    #Close files
    resultspage.close()

if __name__=='__main__':

    from optparse import OptionParser
    parser=OptionParser()
    parser.add_option("-o","--outpath", dest="outpath",help="make page and plots in DIR", metavar="DIR")
    parser.add_option("-d","--data",dest="data",action="append",help="datafile")
    #Optional (all)
    parser.add_option("-i","--inj",dest="injfile",help="SimInsipral injection file",metavar="INJ.XML",default=None)
    parser.add_option("--skyres",dest="skyres",help="Sky resolution to use to calculate sky box size",default=None)
    parser.add_option("--eventnum",dest="eventnum",action="store",default=None,help="event number in SimInspiral file of this signal",type="int",metavar="NUM")
    parser.add_option("--bsn",action="store",default=None,help="Optional file containing the bayes factor signal against noise",type="string")
    parser.add_option("--bci",action="store",default=None,help="Optional file containing the bayes factor coherent signal model against incoherent signal model.",type="string")
    parser.add_option("--dievidence",action="store_true",default=False,help="Calculate the direct integration evidence for the posterior samples")
    parser.add_option("--boxing",action="store",default=64,help="Boxing parameter for the direct integration evidence calculation",type="int",dest="boxing")
    parser.add_option("--evidenceFactor",action="store",default=1.0,help="Overall factor (normalization) to apply to evidence",type="float",dest="difactor",metavar="FACTOR")
    #NS
    parser.add_option("--ns",action="store_true",default=False,help="(inspnest) Parse input as if it was output from parallel nested sampling runs.")
    parser.add_option("--Nlive",action="store",default=None,help="(inspnest) Number of live points used in each parallel nested sampling run.",type="int")
    parser.add_option("--xflag",action="store_true",default=False,help="(inspnest) Convert x to iota.")
    #SS
    parser.add_option("--ss",action="store_true",default=False,help="(SPINspiral) Parse input as if it was output from SPINspiral.")
    parser.add_option("--spin",action="store_true",default=False,help="(SPINspiral) Specify spin run (15 parameters). ")
    parser.add_option("--deltaLogL",action="store",default=None,help="(SPINspiral and LALInferenceMCMC) Difference in logL to use for convergence test.",type="float")
    #LALInf
    parser.add_option("--lalinfmcmc",action="store_true",default=False,help="(LALInferenceMCMC) Parse input from LALInferenceMCMC.")
    parser.add_option("--downsample",action="store",default=None,help="(LALInferenceMCMC) approximate number of samples to record in the posterior",type="int")
    #FM
    parser.add_option("--fm",action="store_true",default=False,help="(followupMCMC) Parse input as if it was output from followupMCMC.")
    # ACF plots off?
    parser.add_option("--no-acf", action="store_true", default=False, dest="noacf")
    (opts,args)=parser.parse_args()

    #List of parameters to plot/bin . Need to match (converted) column names.
    oneDMenu=['mtotal','m1','m2','mchirp','mc','distance','distMPC','iota','psi','eta','ra','dec','a1','a2','phi1','theta1','phi2','theta2','chi','dphi0','dphi1','dphi2','dphi3','dphi4','dphi5','dphi5l','dphi6','dphi6l','dphi7','long','lat','dist','m']
    #List of parameter pairs to bin . Need to match (converted) column names.
    twoDGreedyMenu=[]
    for i in range(0,len(oneDMenu)):
        for j in range(i+1,len(oneDMenu)):
            twoDGreedyMenu.append([oneDMenu[i],oneDMenu[j]])
    #print "twoDGreedyMenu "+ str(twoDGreedyMenu)+"\n"
    # twoDGreedyMenu=[['mc','eta'],['mchirp','eta'],['m1','m2'],['mtotal','eta'],['distance','iota'],['dist','iota'],['dist','m1'],['ra','dec']]
    #Bin size/resolution for binning. Need to match (converted) column names.
    greedyBinSizes={'mc':0.025,'m1':0.1,'m2':0.1,'mass1':0.1,'mass2':0.1,'mtotal':0.1,'eta':0.001,'iota':0.01,'time':1e-4,'distance':1.0,'dist':1.0,'mchirp':0.025,'a1':0.02,'a2':0.02,'phi1':0.05,'phi2':0.05,'theta1':0.05,'theta2':0.05,'ra':0.05,'dec':0.05,'chi':0.05,'dphi3':0.5,'m':0.025}
    #Confidence levels
    confidenceLevels=[0.67,0.9,0.95,0.99]
    #2D plots list
    #twoDplots=[['mc','eta'],['mchirp','eta'],['mc', 'time'],['mchirp', 'time'],['m1','m2'],['mtotal','eta'],['distance','iota'],['dist','iota'],['RA','dec'],['ra', 'dec'],['m1','dist'],['m2','dist'],['mc', 'dist'],['psi','iota'],['psi','distance'],['psi','dist'],['psi','phi0'], ['a1', 'a2'], ['a1', 'iota'], ['a2', 'iota'],['eta','time'],['ra','iota'],['dec','iota'],['chi','iota'],['chi','mchirp'],['chi','eta'],['chi','distance'],['chi','ra'],['chi','dec'],['chi','psi']]
    twoDplots=twoDGreedyMenu

    cbcBayesPostProc(
                        opts.outpath,opts.data,oneDMenu,twoDGreedyMenu,
                        greedyBinSizes,confidenceLevels,twoDplots,
                        #optional
                        injfile=opts.injfile,eventnum=opts.eventnum,skyres=opts.skyres,
                        # direct integration evidence
                        dievidence=opts.dievidence,boxing=opts.boxing,difactor=opts.difactor,
                        #manual bayes factor entry
                        bayesfactornoise=opts.bsn,bayesfactorcoherent=opts.bci,
                        #nested sampling options
                        ns_flag=opts.ns,ns_xflag=opts.xflag,ns_Nlive=opts.Nlive,
                        #spinspiral/mcmc options
                        ss_flag=opts.ss,ss_deltaLogL=opts.deltaLogL,ss_spin_flag=opts.spin,
                        #LALInferenceMCMC options
                        li_flag=opts.lalinfmcmc,nDownsample=opts.downsample,
                        #followupMCMC options
                        fm_flag=opts.fm,
                        # Turn of ACF?
                        noacf=opts.noacf
                    )
#
