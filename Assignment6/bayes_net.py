# YOU THERE!! STOP CHEATING OFF OF THIS! #

##########################################
#	Bayes Net Disease Predictor	 #
#	     Brennan McConnell		 #
##########################################

NO_REASONING = 0
SIBLING = 3
PR = 1
DR = 2
INT_CAUS = 4
COMBINED = 5
NEITHER = 6

class Node(object):

	def __init__(self, name, cpn):
		self.name = name
		self.probs = {}
		self.parents = {}
		self.children = {}
		self.marginal_prob_calculated = False
		self.marginal_probability_name = cpn
		self.marginal_probability = None

	def add_probability(self, key, value):
		self.probs[key] = value

	def add_parent(self, node):
		self.parents[node.name] = node

	def add_child(self, node):
		self.children[node.name] = node


class Bayesian_Network(object):

	def __init__(self):
		self.nodes = {}

	def add_node(self, node):
		self.nodes[node.name] = node

	def calculate_marginal_probabilities(self):
		for RV in self.nodes.values():
			if RV.marginal_prob_calculated == False:
				self.solve_marginal_prob(RV)

	def solve_marginal_prob(self, RV):
		if (len(RV.parents) == 0):
			results = RV.probs.values()
			if (len(results) != 1):
				print "ERROR FOUND!"
			else:
				RV.marginal_probability = results[0]
				RV.marginal_prob_calculated = True
		else:
			RV_marg_prob = 0.0
			rvp_marg_probs = {}
			for rvp in RV.parents.values():
				if (rvp.marginal_prob_calculated == False):
					self.solve_marginal_prob(rvp)
				rvp_marg_probs[rvp.marginal_probability_name] = rvp.marginal_probability

			for (key, val) in RV.probs.items():
				cur = 1.0
				negate = False
				for char in key:
					if (char == '~'):
						negate = True
					else:
						if (negate == False):
							cur *= rvp_marg_probs[char]
						else:
							negate = False
							cur *= (1 - rvp_marg_probs[char])
				RV_marg_prob += val * cur

			RV.marginal_probability = RV_marg_prob
			RV.marginal_prob_calculated = True


	def solve_conditional_probability(self, RV1, RV2, r1status, r2status):
		# Solve P(RV1 | RV2)
		reasoning = self.decide_direction_of_reasoning(RV1, RV2)
		if (reasoning == PR): 
			
			if (RV1.probs.has_key(RV2.marginal_probability_name)): # freebie pretty much, given in initial data
				if r1status == "~":
					return 1-RV1.probs[r2status + RV2.marginal_probability_name]
				else:
					return RV1.probs[r2status + RV2.marginal_probability_name]


			else: # We need to sum something out

				if not (RV1.parents.has_key(RV2.name)): # we are two nodes below the parent
					rvp = None
					for parent in RV1.parents.values():
						rvp = parent
					x = self.solve_conditional_probability(RV1, rvp, r1status, "")
					r1 = self.solve_conditional_probability(rvp, RV2, "", r2status)
					y = self.solve_conditional_probability(RV1, rvp, r1status, "~")
					r2 = 1-r1

					return (x*r1) + (y*r2)

				else: # We are 1 node below the parent
					# Sum out RV1's parents
					rvp_prob_to_sum_out = None
					rvp_marg_conditioning_on = RV2.name

					for rvp in RV1.parents.values():
						if (rvp.name != RV2.name):
							rvp_prob_to_sum_out = (rvp.marginal_probability_name, rvp.marginal_probability)
					
					x = ((r2status+RV2.marginal_probability_name+rvp_prob_to_sum_out[0], rvp_prob_to_sum_out[0]+r2status+RV2.marginal_probability_name), RV2.marginal_probability * rvp_prob_to_sum_out[1])
					y = ((r2status+RV2.marginal_probability_name+"~"+rvp_prob_to_sum_out[0], "~"+rvp_prob_to_sum_out[0]+r2status+RV2.marginal_probability_name), RV2.marginal_probability * (1-rvp_prob_to_sum_out[1]))


					r1 = x[1] * RV1.probs.get(x[0][0], RV1.probs.get(x[0][1], False))
					r2 = y[1] * RV1.probs.get(y[0][0], RV1.probs.get(y[0][1], False))

					if r1status == "~":
						return 1 - ((r1 + r2) / RV2.marginal_probability)
					else:
						return (r1 + r2) / RV2.marginal_probability
			
		elif (reasoning == DR):
			# We can use Predictive reasoning to work backwards
			# i.e. P(A|B) = P(B|A)P(A)/P(B)
			x = self.solve_conditional_probability(RV2, RV1, r2status, "")
			x *= RV1.marginal_probability
			x /= RV2.marginal_probability

			if (r1status == "~"):
				return (1-x)
			else:
				return x

		elif (reasoning == NO_REASONING):
			return 1

		elif (reasoning == SIBLING):
			shared_parent = False
			RV3 = None
			for rvp1 in RV1.parents.values():
				for rvp2 in RV2.parents.values():
					if rvp1 == rvp2:
						RV3 = rvp1
						shared_parent = True
						break
			if (shared_parent): # There is intercausal probability affects
				# These two effects depend on each other through there conditional dependence on the parent
			
				x = self.solve_conditional_probability(RV1, RV3, r1status, "")
				r1 = self.solve_conditional_probability(RV3, RV2, "", r2status)
				y = self.solve_conditional_probability(RV1, RV3, r1status, "~")
				r2 = self.solve_conditional_probability(RV3, RV2, "~", r2status)

				return (x*r1) + (y*r2)

			else:
				return RV1.marginal_probability


	def decide_direction_of_reasoning(self, RV1, RV2):
		if (RV1.name == RV2.name):
			return NO_REASONING

		queue = []
		# If RV2 is above RV1, this is Predictive Reasoning
		queue.append(RV1)
		while (len(queue) > 0):
			for result in queue:
				if (result.name == RV2.name):
					# "Predictive Reasoning"
					return PR
				queue.remove(result)
				for item in result.parents.values():
					queue.append(item)


		queue = []
		queue.append(RV2)
		# If RV1 is above RV2, this is Diagnostic Reasoning
		while (len(queue) > 0):
			for result in queue:
				if (result.name == RV1.name):
					# "Diagnostic Reasoning"
					return DR
				queue.remove(result)
				for item in result.parents.values():
					queue.append(item)


		return SIBLING


	def solve_joint_probability_pair(self, RV1, RV2, r1status, r2status):
		# This returns correctly regardless of dependence between RV1 and RV2
		if r2status == "~":
			mp = 1 - RV2.marginal_probability
		else:
			mp = RV2.marginal_probability

		return mp * self.solve_conditional_probability(RV1, RV2, r1status, r2status)


	def solve_conditional_on_joint_probability(self, RV1, RV2, RV3, r1s, r2s, r3s): #Signifies multiple evidence
		RV_arr = [RV1, RV2, RV3]
		RV_status_arr = [r1s, r2s, r3s]
		#find which variable the other two depend on
		reasoning = self.determine_reasoning_with_mult_evidence(RV_arr)

		if reasoning[0] == INT_CAUS:

			# Can we just solve it given initial data (i.e. P(c|s, p) )
			if (RV1.probs.has_key(r2s+RV2.marginal_probability_name+r3s+RV3.marginal_probability_name) or RV1.probs.has_key(r3s+RV3.marginal_probability_name+r2s+RV2.marginal_probability_name)): # freebie pretty much, given in initial data
					return RV1.probs.get(r2s+RV2.marginal_probability_name+r3s+RV3.marginal_probability_name, RV1.probs.get(r3s+RV3.marginal_probability_name+r2s+RV2.marginal_probability_name, False))

			RVS_not_root = []
			RV_root = reasoning[1]
			RV_root_id = None
			for i in range(0, len(RV_arr)):
				if RV_arr[i] != RV_root:
					RVS_not_root.append(i)
				else:
					RV_root_id = i

			RV_explaining_away_id = None
			if (RV_root_id == 2):
				RV_explaining_away_id = 3
			else:
				RV_explaining_away_id = 2

			if (r1s == "~"):
				probability = 1-RV1.marginal_probability
			else:
				probability = RV1.marginal_probability

			probability *= RV_root.probs.get(RV_status_arr[RVS_not_root[0]]+RV_arr[RVS_not_root[0]].marginal_probability_name+RV_status_arr[RVS_not_root[1]]+RV_arr[RVS_not_root[1]].marginal_probability_name, RV_root.probs.get(RV_status_arr[RVS_not_root[1]]+RV_arr[RVS_not_root[1]].marginal_probability_name+RV_status_arr[RVS_not_root[0]]+RV_arr[RVS_not_root[0]].marginal_probability_name, False))

			probability /= self.solve_conditional_probability(RV_root, RV_arr[RV_explaining_away_id], RV_status_arr[RV_root_id], RV_status_arr[RV_explaining_away_id])
			
		
			return probability


		elif reasoning[0] == COMBINED:
			return None
 
	def determine_reasoning_with_mult_evidence(self, RV_arr):
		rv_as_root = None

		# Check for Intercausal relationship 
		for i in range(0, len(RV_arr)):
			if (RV_arr[i].parents.has_key(RV_arr[(i+1)%3].name) and RV_arr[i].parents.has_key(RV_arr[(i+2)%3].name)):
				rv_as_root = RV_arr[i]
				print "INT_CAUS"
				return (INT_CAUS, rv_as_root)


		# Check for Combined relationship
		for i in range(0, len(RV_arr)):
			if (RV_arr[i].parents.has_key(RV_arr[(i+1)%3].name) and RV_arr[i].children.has_key(RV_arr[(i+2)%3].name)) or (RV_arr[i].children.has_key(RV_arr[(i+1)%3].name) and RV_arr[i].parents.has_key(RV_arr[(i+2)%3].name)) :
				rv_as_root = RV_arr[i]
				print "COMBINED"
				return (COMBINED, RV_arr[i])

		return (NEITHER, None)



def construct_bayes_net():
	P = Node("Pollution", "P")
	P.add_probability("P", 0.9)
	S = Node("Smoker", "S")
	S.add_probability("S", 0.3)
	C = Node("Cancer", "C")
	C.add_probability("~PS", 0.05)
	C.add_probability("~P~S", 0.02)
	C.add_probability("PS", 0.03)
	C.add_probability("P~S", 0.001)
	X = Node("XRay", "X")
	X.add_probability("C", 0.9)
	X.add_probability("~C", 0.2)
	D = Node("Dyspnoea", "D")
	D.add_probability("C", 0.65)
	D.add_probability("~C", 0.3)

	C.add_parent(P)
	P.add_child(C)
	C.add_parent(S)
	S.add_child(C)
	X.add_parent(C)
	C.add_child(X)
	D.add_parent(C)
	C.add_child(D)

	BN = Bayesian_Network()
	BN.add_node(P)
	BN.add_node(S)
	BN.add_node(C)
	BN.add_node(X)
	BN.add_node(D)
	BN.calculate_marginal_probabilities()

	print BN.solve_conditional_on_joint_probability(P, C, S, "", "", "")

	return BN


if __name__ == "__main__":
	bayes_net = construct_bayes_net()
#	for node in bayes_net.nodes.values():
#		print node.marginal_probability_name, ":", round(node.marginal_probability, 4)









