import sys
import paddle.fluid.incubate.data_generator as dg

class CriteoDataset(dg.MultiSlotDataGenerator):
    def setup(self, sparse_feature_dim):
        self.cont_min_ = [0, -3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.cont_max_ = [20, 600, 100, 50, 64000, 500, 100, 50, 500, 10, 10, 10, 50]
        self.cont_diff_ = [20, 603, 100, 50, 64000, 500, 100, 50, 500, 10, 10, 10, 50]
        self.hash_dim_ = sparse_feature_dim
        # here, training data are lines with line_index < train_idx_
        self.train_idx_ = 41256555
        self.continuous_range_ = range(1, 14)
        self.categorical_range_ = range(14, 40)

    def _process_line(self, line):
        features = line.rstrip('\n').split('\t')
        dense_feature = []
        sparse_feature = []
        for idx in self.continuous_range_:
            if features[idx] == '':
                dense_feature.append(0.0)
            else:
                dense_feature.append((float(features[idx]) - self.cont_min_[idx - 1]) / \
                                     self.cont_diff_[idx - 1])
        for idx in self.categorical_range_:
            sparse_feature.append([hash(str(idx) + features[idx]) % self.hash_dim_])
            
        return dense_feature, sparse_feature, [int(features[0])]

    def infer_reader(self, filelist, batch, buf_size):
        print(filelist)
        def local_iter():
            for fname in filelist:
                with open(fname.strip(), "r") as fin:
                    for line in fin:
                        dense_feature, sparse_feature, label = self._process_line(line)
                        #yield dense_feature, sparse_feature, label
                        yield [dense_feature] + sparse_feature + [label]
        import paddle
        batch_iter = paddle.batch(
            paddle.reader.shuffle(
                local_iter, buf_size=buf_size),
            batch_size=batch)
        return batch_iter
                        

    def generate_sample(self, line):
        def data_iter():
            dense_feature, sparse_feature, label = self._process_line(line)
            feature_name = ["dense_input"]
            for idx in self.categorical_range_:
                feature_name.append("C" + str(idx - 13))
            feature_name.append("label")
            yield zip(feature_name, [dense_feature] + sparse_feature + [label])

        return data_iter

if __name__ == "__main__":
    criteo_dataset = CriteoDataset()
    criteo_dataset.setup(int(sys.argv[1]))
    criteo_dataset.run_from_stdin()
