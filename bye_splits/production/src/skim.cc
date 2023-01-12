#include "include/skim.h"

// Prepare missing matching
// def deltar(df):
//     df['deta']=df['cl3d_eta']-df['genpart_exeta']
//     df['dphi']=np.abs(df['cl3d_phi']-df['genpart_exphi'])
//     sel=df['dphi']>np.pi
//     df['dphi']-=sel*(2*np.pi)
//     return(np.sqrt(df['dphi']*df['dphi']+df['deta']*df['deta']))

void skim(string tn, string inf, string outf, string particle) {

  YAML::Node config = YAML::LoadFile("bye_splits/production/prod_params.yaml");
  vector<int> vec;
  if (config["disconnectedTriggerLayers"]) {
	vec = config["disconnectedTriggerLayers"].as<std::vector<int>>();
  }
  string reachedEE = "";
  if (config["reachedEE"]) {
	reachedEE = config["reachedEE"].as<string>();
  }

  //ROOT::EnableImplicitMT();
  ROOT::RDataFrame df(tn, inf);
  auto dd = df.Range(0, 100);
  
  vector<string> genvars_int = {"genpart_pid"};
  vector<string> genvars_float = {"genpart_exphi", "genpart_exeta", "genpart_energy"};
  vector<string> genvars = join_vars(genvars_int, genvars_float);
  
  unordered_map<string,string> pmap = {{"photons", "22"},
									   {"electrons", "11"}};
  string condgen = "genpart_gen != -1 && ";
  condgen += "genpart_reachedEE == " + reachedEE;
  condgen += " && genpart_pid == " + pmap[particle];
  condgen += " && genpart_exeta > 0";

  dd = dd.Define("tmp_good_gens", condgen);
  for(auto& v : genvars)
   	dd = dd.Define("tmp_good_" + v, v + "[tmp_good_gens]");

  vector<string> tcvars_int = {"tc_layer", "tc_cellu", "tc_cellv", "tc_waferu", "tc_waferv"};
  vector<string> tcvars_float = {"tc_energy", "tc_mipPt", "tc_pt", 
								 "tc_x", "tc_y", "tc_z", "tc_phi", "tc_eta"};
  vector<string> tcvars = join_vars(tcvars_int, tcvars_float);

  string condtc = "tc_zside == 1";// && tc_layer%2 == 0";
  dd = dd.Define("tmp_good_tcs", condtc);
  for(auto& v : tcvars)
	dd = dd.Define("tmp_good_" + v, v + "[tmp_good_tcs]");

  vector<string> clvars_uint = {"cl3d_id"};
  vector<string> clvars_float = {"cl3d_energy", "cl3d_pt", "cl3d_eta", "cl3d_phi"};
  vector<string> clvars = join_vars(clvars_uint, clvars_float);
	
  string condcl = "cl3d_eta > 0"; //dummy selection
  dd = dd.Define("tmp_good_cl", condcl);
  for(auto& v : clvars)
	dd = dd.Define("tmp_good_" + v, v + "[tmp_good_cl]");

  vector<string> intvars = join_vars(genvars_int, tcvars_int);
  for(auto& var : intvars) {
	dd = dd.Define("good_" + var,
				   [](const ROOT::VecOps::RVec<int> &v) {
					 return std::vector<int>(v.begin(), v.end());
				   },
				   {"tmp_good_" + var});
  }
  vector<string> uintvars = join_vars(clvars_uint);
  for(auto& var : uintvars) {
    dd = dd.Define("good_" + var,
		   [](const ROOT::VecOps::RVec<unsigned> &v) {
		     return std::vector<unsigned>(v.begin(), v.end());
		   },
		   {"tmp_good_" + var});
  }
  vector<string> floatvars = join_vars(genvars_float, tcvars_float, clvars_float);
  for(auto& var : floatvars) {
	dd = dd.Define("good_" + var,
				   [](const ROOT::VecOps::RVec<float> &v) {
					 return std::vector<float>(v.begin(), v.end());
				   },
				   {"tmp_good_" + var});
  }

  vector<string> allvars = join_vars(genvars, tcvars, clvars);
  vector<string> good_allvars = {"event"};
  for(auto& v : allvars)
	good_allvars.push_back("good_" + v);

  dd.Snapshot(tn, outf, good_allvars);
}
